"""Disposable Docker/OpenVPN lab: real TLS tunnel, internal storage, and fail-closed egress.

No SUUMO traffic or production database/configuration is used. Run from the host.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "suumo_source_crawler"))
from scripts.docker_vpn import DockerVpn
from scripts.telegram_control import Host


def run(argv, timeout=60):
    """Keep private TLS material and Compose credentials out of tool/log output."""
    result = subprocess.run(
        list(map(str, argv)), capture_output=True, text=True, timeout=timeout
    )
    if result.returncode:
        raise RuntimeError(
            f"QA command failed ({argv[0]}, exit {result.returncode}): "
            + result.stderr[-800:]
        )
    return result.stdout.strip()


def certificates(root):
    """Generate disposable identities; no supplied VPN credentials enter this lab."""
    run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "2",
            "-keyout",
            root / "ca.key",
            "-out",
            root / "ca.crt",
            "-subj",
            "/CN=suumo-vpn-qa-ca",
        ]
    )
    for name, usage in [("server", "serverAuth"), ("client", "clientAuth")]:
        run(
            [
                "openssl",
                "req",
                "-new",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                root / (name + ".key"),
                "-out",
                root / (name + ".csr"),
                "-subj",
                "/CN=suumo-vpn-qa-" + name,
            ]
        )
        (root / (name + ".ext")).write_text(
            "basicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage="
            + usage
            + "\n"
        )
        run(
            [
                "openssl",
                "x509",
                "-req",
                "-in",
                root / (name + ".csr"),
                "-CA",
                root / "ca.crt",
                "-CAkey",
                root / "ca.key",
                "-CAcreateserial",
                "-out",
                root / (name + ".crt"),
                "-days",
                "2",
                "-extfile",
                root / (name + ".ext"),
            ]
        )
    for path in root.iterdir():
        path.chmod(0o600)


def main():
    """Prove host isolation and a fail-closed worker namespace before deployment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="suumo-vpn-docker-qa:local")
    args = parser.parse_args()
    project = "suumo_vpn_qa_" + uuid.uuid4().hex[:10]
    containers = []
    with tempfile.TemporaryDirectory(prefix=project, dir=ROOT / "tmp") as directory:
        root = Path(directory)
        compose_file = root / "docker-compose.release.yml"
        compose_file.write_bytes((ROOT / "docker-compose.release.yml").read_bytes())
        values = {
            "RELEASE_COMPOSE_PROJECT_NAME": project,
            "SUUMO_CRAWLER_IMAGE": args.image.rsplit(":", 1)[0],
            "SUUMO_CRAWLER_TAG": args.image.rsplit(":", 1)[1],
            "SUUMO_VPN_BACKEND": "docker",
            "POSTGRES_USER": "qa",
            "POSTGRES_PASSWORD": "qa-disposable-password",
            "POSTGRES_DB": "qa",
            "POSTGRES_PORT": "0",
            "MINIO_API_PORT": "0",
            "MINIO_CONSOLE_PORT": "0",
            "MINIO_ROOT_USER": "qa-admin",
            "MINIO_ROOT_PASSWORD": "qa-disposable-password",
            "VPN_MEM_LIMIT": "256m",
            "VPN_CPUS": "1",
        }
        env = root / ".env"
        env.write_text("".join(k + "=" + v + "\n" for k, v in values.items()))
        env.chmod(0o600)
        host = Host(env, compose_file, values)
        compose = host.compose
        try:
            run([*compose, "up", "-d", "--wait", "postgres", "minio"], timeout=120)
            controller = DockerVpn(host)
            network = controller.config["networks"]["release_net"]["name"]
            tls = root / "tls"
            tls.mkdir(mode=0o700)
            certificates(tls)
            (tls / "server.conf").write_text(
                "dev tun0\nproto tcp-server\nport 1194\nserver 10.91.0.0 255.255.255.0\ntopology subnet\nca /qa/ca.crt\ncert /qa/server.crt\nkey /qa/server.key\ndh none\nremote-cert-tls client\ndata-ciphers AES-256-GCM:AES-128-GCM\nkeepalive 2 10\nverb 2\n"
            )
            server = run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--network",
                    network,
                    "--cap-add",
                    "NET_ADMIN",
                    "--device",
                    "/dev/net/tun",
                    "-v",
                    str(tls) + ":/qa:ro",
                    "--entrypoint",
                    "openvpn",
                    args.image,
                    "--config",
                    "/qa/server.conf",
                ]
            )
            containers.append(server)
            server_ip = json.loads(
                run(
                    [
                        "docker",
                        "inspect",
                        "--format",
                        "{{json .NetworkSettings.Networks}}",
                        server,
                    ]
                )
            )[network]["IPAddress"]
            fixture = run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--network",
                    "container:" + server,
                    "--cap-drop",
                    "ALL",
                    "--entrypoint",
                    "python",
                    args.image,
                    "-m",
                    "http.server",
                    "18080",
                    "--bind",
                    "0.0.0.0",
                ]
            )
            containers.append(fixture)
            before = run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "host",
                    "--entrypoint",
                    "ip",
                    args.image,
                    "-j",
                    "-4",
                    "route",
                ]
            )
            profile = (
                "client\ndev tun\nproto tcp\nremote "
                + server_ip
                + " 1194\nremote-cert-tls server\n"
            )
            for tag, name in [
                ("ca", "ca.crt"),
                ("cert", "client.crt"),
                ("key", "client.key"),
            ]:
                profile += (
                    "<" + tag + ">\n" + (tls / name).read_text() + "</" + tag + ">\n"
                )
            controller.prepare(profile.encode(), "qa.ovpn")
            controller.start()
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and not controller.health()[0]:
                time.sleep(1)
            if not controller.health()[0]:
                # Show only public network diagnostics, never OpenVPN configuration.
                print(
                    "VPN namespace",
                    run(["docker", "exec", controller.ids()[0], "ip", "-j", "route"]),
                    flush=True,
                )
                print(
                    "VPN firewall",
                    run(
                        [
                            "docker",
                            "exec",
                            controller.ids()[0],
                            "iptables",
                            "-S",
                            "OUTPUT",
                        ]
                    ),
                    flush=True,
                )
                raise AssertionError("Local real TLS VPN did not become healthy")
            worker = run(
                [
                    *compose,
                    "run",
                    "-d",
                    "--no-deps",
                    "--entrypoint",
                    "python",
                    "suumo-links",
                    "-c",
                    "import time;time.sleep(600)",
                ]
            )
            containers.append(worker)
            vpn = controller.ids()[0]
            namespace = "import os;print(os.readlink('/proc/self/ns/net'))"
            assert run(["docker", "exec", vpn, "python", "-c", namespace]) == run(
                ["docker", "exec", worker, "python", "-c", namespace]
            )
            infra = run([*compose, "ps", "-q", "postgres"])
            assert (
                json.loads(
                    run(
                        [
                            "docker",
                            "inspect",
                            "--format",
                            "{{json .HostConfig.NetworkMode}}",
                            infra,
                        ]
                    )
                )
                != "container:" + vpn
            )
            probe = """import io,json,socket,urllib.request,psycopg
from minio import Minio
with psycopg.connect(host='postgres',user='qa',password='qa-disposable-password',dbname='qa') as c:
 assert c.execute('SELECT 1').fetchone()==(1,)
m=Minio('minio:9000',access_key='qa-admin',secret_key='qa-disposable-password',secure=False)
m.make_bucket('qa-probe');m.put_object('qa-probe','probe',io.BytesIO(b'QA'),2)
r=m.get_object('qa-probe','probe');assert r.read()==b'QA';r.close();r.release_conn()
assert urllib.request.urlopen('http://10.91.0.1:18080/',timeout=5).status==200
assert socket.gethostbyname('postgres')!='127.0.0.1'
assert '127.0.0.11' not in open('/etc/resolv.conf').read()
print('TLS tunnel, shared namespace, PostgreSQL/MinIO read-write and DNS configuration: PASS')
"""
            print(run(["docker", "exec", worker, "python", "-c", probe]), flush=True)
            blocked = """import socket
s=socket.socket();s.settimeout(2)
try: s.connect(('SERVER_IP',18080))
except OSError: print('direct transport blocked: PASS')
else: raise AssertionError('VPN worker bypassed tunnel')
finally: s.close()
""".replace("SERVER_IP", server_ip)
            print(run(["docker", "exec", worker, "python", "-c", blocked]), flush=True)
            # Simulate tunnel failure while retaining the worker and its network namespace.
            pid = run(["docker", "exec", vpn, "cat", "/run/openvpn.pid"])
            run(
                [
                    "docker",
                    "exec",
                    vpn,
                    "python",
                    "-c",
                    "import os,signal;os.kill(" + pid + ",signal.SIGSTOP)",
                ]
            )
            run(["docker", "exec", vpn, "ip", "link", "set", "tun0", "down"])
            for route in ("0.0.0.0/1", "128.0.0.0/1"):
                if json.loads(
                    run(["docker", "exec", vpn, "ip", "-j", "route", "show", route])
                ):
                    run(["docker", "exec", vpn, "ip", "route", "del", route])
            assert not controller.health()[0]
            print(run(["docker", "exec", worker, "python", "-c", blocked]), flush=True)
            counter = run(
                ["docker", "exec", vpn, "iptables", "-L", "OUTPUT", "-n", "-v", "-x"]
            )
            assert (
                "policy DROP" in counter
                and int(counter.split("policy DROP ")[1].split()[0]) > 0
            )
            run(
                [
                    "docker",
                    "exec",
                    vpn,
                    "python",
                    "-c",
                    "import os,signal;os.kill(" + pid + ",signal.SIGCONT)",
                ]
            )
            assert controller.stop(sleeper=lambda seconds: None)
            # Removal of the VPN sidecar does not give a surviving worker normal Internet.
            print(run(["docker", "exec", worker, "python", "-c", blocked]), flush=True)
            after = run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "host",
                    "--entrypoint",
                    "ip",
                    args.image,
                    "-j",
                    "-4",
                    "route",
                ]
            )
            assert json.loads(before) == json.loads(after)
            print(
                "tunnel failure, sidecar removal, default-DROP counters, and unchanged host routes: PASS",
                flush=True,
            )
        finally:
            # Every removed container/volume is created by this unique disposable lab.
            for cid in reversed(containers):
                subprocess.run(
                    ["docker", "rm", "-f", cid], capture_output=True, timeout=30
                )
            subprocess.run(
                [
                    *compose,
                    "--profile",
                    "tasks",
                    "down",
                    "--volumes",
                    "--remove-orphans",
                ],
                capture_output=True,
                timeout=60,
            )
    print(
        "Docker VPN local acceptance: PASS (no SUUMO or production writes)", flush=True
    )


if __name__ == "__main__":
    main()
