"""Host controller for the isolated Compose VPN; never alter host routes or tunnels."""

import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time


def docker_backend(values):
    """Keep legacy releases compatible, requiring an explicit switch at deployment."""
    backend = values.get("SUUMO_VPN_BACKEND", "host")
    if backend not in {"host", "docker"}:
        raise ValueError("SUUMO_VPN_BACKEND must be host or docker")
    return backend == "docker"


class DockerVpn:
    """Resolve only the configured project's VPN and use bounded Docker commands."""

    def __init__(self, host, runner=None):
        """Cache Compose identity without exposing its credential-bearing config."""
        self.host = host
        self.runner = runner or self.run
        config = self.call(
            [*host.compose, "--profile", "tasks", "config", "--format", "json"]
        )
        self.config = json.loads(config.stdout)
        self.project = self.config["name"]
        vpn = self.config["services"].get("vpn", {})
        if (
            vpn.get("network_mode") == "host"
            or vpn.get("privileged")
            or vpn.get("ports")
            or not vpn
        ):
            raise RuntimeError("VPN must use an isolated container network")
        for name in ("suumo-links", "suumo-html", "suumo-page", "suumo-rerun-html"):
            service = self.config["services"].get(name, {})
            if (
                service.get("network_mode") != "service:vpn"
                or service.get("privileged")
                or service.get("cap_add")
            ):
                raise RuntimeError(
                    "Crawler must share VPN network without elevated capabilities"
                )
        self.runtime = Path(
            host.values.get("VPN_RUNTIME_DIR")
            or host.env_file.parent / "state/vpn-runtime"
        )
        if not self.runtime.is_absolute():
            self.runtime = host.env_file.parent / self.runtime

    @staticmethod
    def run(argv, timeout):
        """Do not inherit stdin or an accidentally exported release image tag."""
        environment = dict(os.environ)
        environment.pop("SUUMO_CRAWLER_TAG", None)
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
            stdin=subprocess.DEVNULL,
        )

    def call(self, argv, timeout=15, required=True):
        """Report only command identity and exit code, never credential-bearing output."""
        result = self.runner(list(argv), timeout)
        if required and result.returncode:
            raise RuntimeError(
                f"VPN Docker command failed: {argv[0]} (exit {result.returncode})"
            )
        return result

    def ids(self, all_containers=False, timeout=15):
        """Find only the VPN container labelled with this Compose project."""
        return self.call(
            [
                "docker",
                "ps",
                "-aq" if all_containers else "-q",
                "--filter",
                "label=com.docker.compose.project=" + self.project,
                "--filter",
                "label=com.docker.compose.service=vpn",
            ],
            timeout=timeout,
        ).stdout.split()

    def stopped(self):
        """A Docker inspection error is not evidence that the VPN has stopped."""
        return not self.ids()

    def stop(self, sleeper=time.sleep):
        """Stop/remove the scoped sidecar and verify absence over three observations."""
        for _ in range(3):
            ids = self.ids(True)
            if ids:
                self.call(["docker", "stop", "--time", "10", *ids], timeout=35)
                self.call(["docker", "rm", *ids])
            for check in range(3):
                if not self.stopped():
                    break
                if check == 2:
                    return True
                sleeper(2)
        return False

    def health(self, timeout=5):
        """Verify exactly one running sidecar and inspect its private namespace."""
        deadline = time.monotonic() + timeout
        ids = self.ids(timeout=timeout)
        if len(ids) != 1:
            return False, "VPN container is not running"
        result = self.call(
            [
                "docker",
                "exec",
                ids[0],
                "python",
                "/app/vpn/container_vpn.py",
                "--health",
            ],
            timeout=max(0.1, deadline - time.monotonic()),
            required=False,
        )
        return (
            result.returncode == 0,
            "Docker tunnel/routes/firewall verified"
            if result.returncode == 0
            else "Docker VPN is not healthy",
        )

    def internal_ip(self, service):
        """Resolve infra addresses on the exact network used by the VPN sidecar."""
        cid = self.call([*self.host.compose, "ps", "-q", service]).stdout.strip()
        if not cid:
            raise RuntimeError("Infra must be running before VPN preflight")
        networks = json.loads(
            self.call(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{json .NetworkSettings.Networks}}",
                    cid,
                ]
            ).stdout
        )
        names = {
            self.config["networks"][name]["name"]
            for name in self.config["services"]["vpn"]["networks"]
        }
        matches = [row["IPAddress"] for name, row in networks.items() if name in names]
        if len(matches) != 1:
            raise RuntimeError("VPN and infra must share exactly one private network")
        return str(ipaddress.IPv4Address(matches[0]))

    def prepare(self, data, filename):
        """Write a frozen config, internal hosts, and tunnel DNS before creating the sidecar."""
        from scripts.deploy_release import atomic_write
        from scripts.vpn_pool import profile

        profile(data, filename)
        text = data.decode()
        directives = [
            shlex.split(line, comments=True)
            for line in re.sub(
                r"<(ca|cert|key)>.*?</\1>", "", text, flags=re.S
            ).splitlines()
        ]
        remote = next(words for words in directives if words and words[0] == "remote")
        proto = next(words[1] for words in directives if words and words[0] == "proto")
        context = {
            "remote": str(ipaddress.IPv4Address(remote[1])),
            "port": int(remote[2]),
            "protocol": "udp" if proto == "udp" else "tcp",
            "postgres": self.internal_ip("postgres"),
            "minio": self.internal_ip("minio"),
        }
        # No profile-supplied route can accidentally bypass the tunnel.
        text = re.sub(
            r"(?m)^\s*(dev|redirect-gateway|route|verb|data-ciphers|cipher)\s+[^\n]*$",
            "",
            text,
        )
        cipher = next(
            (w[1] for w in directives if w and w[0] == "cipher"), "AES-128-CBC"
        )
        if cipher not in {"AES-128-CBC", "AES-256-CBC", "AES-128-GCM", "AES-256-GCM"}:
            raise ValueError("Unsupported VPN cipher")
        text = (
            text.rstrip()
            + '\ndev tun0\nredirect-gateway def1\npull-filter ignore "route "\npull-filter ignore "redirect-gateway"\npull-filter ignore "dhcp-option"\ndata-ciphers AES-256-GCM:AES-128-GCM:AES-256-CBC:AES-128-CBC\ndata-ciphers-fallback '
            + cipher
            + "\n"
        )
        if self.runtime.is_symlink():
            raise ValueError("VPN runtime root cannot be a symlink")
        self.runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.runtime.chmod(0o700)
        for name, payload in {
            "config.ovpn": text,
            "context.json": json.dumps(context),
            "hosts": "127.0.0.1 localhost\n"
            + context["postgres"]
            + " postgres\n"
            + context["minio"]
            + " minio\n",
            "resolv.conf": "nameserver 1.1.1.1\nnameserver 8.8.8.8\noptions timeout:2 attempts:2\n",
        }.items():
            atomic_write(self.runtime / name, payload.encode(), 0o600)

    def start(self, timeout=30):
        """Do not pull, auto-start dependencies, restart on boot, or reuse an old namespace."""
        self.call(
            [
                *self.host.compose,
                "up",
                "-d",
                "--no-deps",
                "--pull",
                "never",
                "--force-recreate",
                "vpn",
            ],
            timeout=timeout,
        )
