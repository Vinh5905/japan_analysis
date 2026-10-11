"""OpenVPN client supervisor and fail-closed firewall in a private network namespace."""

import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

CONTEXT = Path("/vpn/context.json")
PID = Path("/run/openvpn.pid")


def command(argv):
    """Bound network inspection and setup without printing configuration secrets."""
    return subprocess.run(argv, capture_output=True, text=True, check=True, timeout=5)


def firewall_rules(context):
    """Permit only loopback, VPN transport, tunnel traffic, and exact internal services."""
    remote = str(ipaddress.IPv4Address(context["remote"]))
    port = int(context["port"])
    if not 1 <= port <= 65535 or context["protocol"] not in {"tcp", "udp"}:
        raise ValueError("Invalid VPN transport")
    rules = [
        ["-o", "lo", "-j", "ACCEPT"],
        ["-o", "tun0", "-j", "ACCEPT"],
        ["-d", remote, "-p", context["protocol"], "--dport", str(port), "-j", "ACCEPT"],
    ]
    for service, port in [("postgres", 5432), ("minio", 9000)]:
        address = str(ipaddress.IPv4Address(context[service]))
        rules.append(["-d", address, "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"])
    return rules


def install_firewall(context):
    """Default DROP precedes all exceptions; no generic established-connection bypass."""
    for binary in ("iptables", "ip6tables"):
        command([binary, "-w", "2", "-P", "OUTPUT", "DROP"])
        command([binary, "-w", "2", "-P", "FORWARD", "DROP"])
        command([binary, "-w", "2", "-F", "OUTPUT"])
    for rule in firewall_rules(context):
        command(["iptables", "-w", "2", "-A", "OUTPUT", *rule])
    # Preserve internal connectivity even if the VPN server advertises overlapping routes.
    for name in ("postgres", "minio"):
        command(["ip", "route", "replace", context[name] + "/32", "dev", "eth0"])


def health():
    """Check the child, tunnel, redirect routes, and complete outbound firewall policy."""
    try:
        context = json.loads(CONTEXT.read_text())
        pid = int(PID.read_text())
        os.kill(pid, 0)
        if Path(f"/proc/{pid}/comm").read_text().strip() != "openvpn":
            return False
        links = json.loads(command(["ip", "-j", "link", "show", "tun0"]).stdout)
        if not links or "UP" not in links[0]["flags"]:
            return False
        for network in ("0.0.0.0/1", "128.0.0.0/1"):
            routes = json.loads(
                command(["ip", "-j", "-4", "route", "show", network]).stdout
            )
            if not any(
                r.get("dst") == network and r.get("dev") == "tun0" for r in routes
            ):
                return False
        expected = ["-P OUTPUT DROP"] + [
            "-A OUTPUT " + " ".join(rule) for rule in firewall_rules(context)
        ]
        # iptables prints protocol modules in its canonical representation.
        actual = command(["iptables", "-w", "2", "-S", "OUTPUT"]).stdout.splitlines()
        actual = [r.replace(" -m tcp ", " ").replace(" -m udp ", " ") for r in actual]
        actual = [re.sub(r"(\d+\.\d+\.\d+\.\d+)/32", r"\1", r) for r in actual]
        if (
            actual != expected
            or command(["ip6tables", "-w", "2", "-S", "OUTPUT"]).stdout.strip()
            != "-P OUTPUT DROP"
        ):
            return False
        return True
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return False


def main():
    """Keep firewall rules intact on disconnect; workers cannot bypass a failed tunnel."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()
    if args.health:
        return 0 if health() else 1
    child = None
    try:
        context = json.loads(CONTEXT.read_text())
        install_firewall(context)
        child = subprocess.Popen(
            ["openvpn", "--config", "/vpn/config.ovpn", "--verb", "2", "--disable-dco"]
        )
        PID.write_text(str(child.pid))

        def terminate(signum, frame):
            """Forward container shutdown without removing the firewall."""
            if child.poll() is None:
                child.terminate()

        signal.signal(signal.SIGTERM, terminate)
        signal.signal(signal.SIGINT, terminate)
        return child.wait()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(
            "VPN container failed: " + type(exc).__name__, file=sys.stderr, flush=True
        )
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
