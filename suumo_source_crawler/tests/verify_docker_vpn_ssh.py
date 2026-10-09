"""Verify fresh host SSH and PostgreSQL/MinIO tunnels while QA Docker VPN is active."""
import argparse
import json
import shlex
import socket
import struct
import subprocess
import time
from urllib.request import urlopen


def free_port():
    """Allocate a temporary loopback port without changing an existing tunnel."""
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    """Keep a new SSH session alive only for the connectivity checks and acknowledgement."""
    parser = argparse.ArgumentParser()
    parser.add_argument('qadir')
    args = parser.parse_args()
    assert args.qadir.startswith('/opt/suumo-crawler/tmp/docker-vpn-qa-')
    ports = [free_port() for _ in range(3)]
    options = ['-o', 'ControlMaster=no', '-o', 'ControlPath=none', '-o', 'ConnectTimeout=10']
    argv = ['ssh', *options, '-o', 'ExitOnForwardFailure=yes', '-N']
    for local, remote in zip(ports, (5432, 9000, 9001)):
        argv.extend(['-L', f'127.0.0.1:{local}:127.0.0.1:{remote}'])
    process = subprocess.Popen([*argv, 'thuevpsgiare'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 20
        while True:
            assert process.poll() is None, 'Fresh SSH tunnel exited'
            try:
                with socket.create_connection(('127.0.0.1', ports[0]), timeout=3) as sock:
                    sock.sendall(struct.pack('!II', 8, 80877103))
                    assert sock.recv(1) in (b'S', b'N'), 'PostgreSQL protocol not reachable'
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.5)
        for port, path in ((ports[1], '/minio/health/live'), (ports[2], '/')):
            with urlopen(f'http://127.0.0.1:{port}{path}', timeout=10) as response:
                assert response.status == 200
        code = 'from pathlib import Path; import subprocess; assert subprocess.run(["ip","link","show","tun0"],capture_output=True).returncode != 0; Path(' + repr(args.qadir + '/ssh-probe-ok') + ').write_text("SSH new session; PostgreSQL protocol; MinIO API and console: PASS")'
        subprocess.run(['ssh', *options, 'thuevpsgiare', 'python3 -c ' + shlex.quote(code)], check=True, timeout=20)
        print(json.dumps({'fresh_ssh': True, 'postgres_tunnel': True, 'minio_api_tunnel': True, 'minio_console_tunnel': True, 'host_tun_absent': True}))
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == '__main__':
    main()
