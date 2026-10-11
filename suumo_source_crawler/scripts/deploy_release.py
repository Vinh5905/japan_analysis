#!/usr/bin/env python3
"""Package host runtime locally, then explicitly deploy it over an SSH alias."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.runtime_lock import release_lock  # noqa: E402


SERVICE = "suumo-crawler-pipeline.service"
TIMER = "suumo-crawler-pipeline.timer"
DISPATCH_SERVICE = "suumo-crawler-dispatch.service"
REFRESH_SERVICE = "suumo-crawler-refresh-areas.service"
BOT_SERVICE = "suumo-crawler-telegram.service"
UNIT_PREFIX = "suumo_source_crawler/deploy/systemd/"
# Explicit allowlist: never copy .env, VPN keys, tmp, warehouse or data volumes.
HOST_FILES = (
    "docker-compose.release.yml",
    "suumo_source_crawler/scripts/__init__.py",
    "suumo_source_crawler/scripts/run_release_pipeline.py",
    "suumo_source_crawler/scripts/ensure_openvpn.py",
    "suumo_source_crawler/scripts/stop_openvpn.py",
    "suumo_source_crawler/scripts/runtime_lock.py",
    "suumo_source_crawler/scripts/telegram_state.py",
    "suumo_source_crawler/scripts/telegram_control.py",
    "suumo_source_crawler/scripts/telegram_ui.py",
    "suumo_source_crawler/scripts/crawl_dispatcher.py",
    "suumo_source_crawler/scripts/area_catalog.py",
    "suumo_source_crawler/scripts/area_names.json",
    "suumo_source_crawler/scripts/refresh_areas.py",
    "suumo_source_crawler/scripts/vpn_pool.py",
    "suumo_source_crawler/scripts/docker_vpn.py",
    "docker/postgres/migrations/008_crawl_areas_and_pipeline.sql",
    "docker/postgres/migrations/009_crawl_vpn_pool.sql",
    UNIT_PREFIX + DISPATCH_SERVICE,
    UNIT_PREFIX + REFRESH_SERVICE,
    "suumo_source_crawler/scripts/deploy_release.py",
    "suumo_source_crawler/crawler/crawler/__init__.py",
    "suumo_source_crawler/crawler/crawler/telegram_notifier.py",
    UNIT_PREFIX + SERVICE,
    UNIT_PREFIX + TIMER,
    UNIT_PREFIX + BOT_SERVICE,
)


def validate_tag(tag: str) -> str:
    """Require an explicit Docker tag so a release can be reproduced."""
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", tag) or tag == "latest":
        raise ValueError(
            "Use an explicit image tag, e.g. 20261009-01 or a commit SHA; latest is not accepted"
        )
    return tag


def validate_target(value: str) -> Path:
    """Accept a non-root absolute path safe for systemd's unquoted command paths."""
    if (
        not re.fullmatch(r"/[A-Za-z0-9_./-]+", value)
        or ".." in Path(value).parts
        or value == "/"
    ):
        raise ValueError(
            "Target must be an absolute non-root path without spaces or .."
        )
    return Path(value)


def build_bundle(tag: str, output: Path, root: Path = REPOSITORY_ROOT) -> Path:
    """Write the complete host allowlist and checksums without runtime secrets."""
    validate_tag(tag)
    payloads = {name: (root / name).read_bytes() for name in HOST_FILES}
    manifest = {
        "format": 1,
        "tag": tag,
        "files": {
            name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()
        },
    }
    payloads["manifest.json"] = json.dumps(manifest, indent=2).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for name, data in payloads.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    return output


def unpack_bundle(bundle: Path, destination: Path) -> str:
    """Verify the entire archive before writing any managed release files."""
    with tarfile.open(bundle, "r:gz") as archive:
        members = archive.getmembers()
        expected = set(HOST_FILES) | {"manifest.json"}
        if len(members) != len(expected) or {item.name for item in members} != expected:
            raise ValueError(
                "Bundle must contain exactly the managed host files and manifest"
            )
        if any(not item.isfile() or item.size > 2_000_000 for item in members):
            raise ValueError("Bundle contains a link, directory or oversized file")
        payloads = {item.name: archive.extractfile(item).read() for item in members}
    manifest = json.loads(payloads.pop("manifest.json"))
    if manifest.get("format") != 1 or set(manifest.get("files", {})) != set(HOST_FILES):
        raise ValueError("Unsupported or incomplete release manifest")
    tag = validate_tag(manifest["tag"])
    for name, data in payloads.items():
        if hashlib.sha256(data).hexdigest() != manifest["files"][name]:
            raise ValueError(f"Checksum mismatch: {name}")
    for name, data in payloads.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return tag


def update_tag(text: str, tag: str) -> str:
    """Replace only the image tag, preserving all other VPS configuration."""
    pattern = r"(?m)^[ \t]*(?:export[ \t]+)?SUUMO_CRAWLER_TAG[ \t]*=.*$"
    updated, count = re.subn(pattern, f"SUUMO_CRAWLER_TAG={validate_tag(tag)}", text)
    if not count:
        updated = text.rstrip("\n") + f"\nSUUMO_CRAWLER_TAG={tag}\n"
    return updated


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a host command with a failing exit code propagated to the caller."""
    if command[:2] == ["docker", "compose"]:
        # The release tag in --env-file wins over an accidentally exported shell tag.
        environment = dict(os.environ)
        environment.pop("SUUMO_CRAWLER_TAG", None)
        kwargs.setdefault("env", environment)
    return subprocess.run(command, check=True, text=True, **kwargs)


def unit_state(unit: str) -> str:
    """Read systemd state without treating an inactive or missing unit as a failure."""
    result = subprocess.run(
        ["systemctl", "is-active", unit], capture_output=True, text=True
    )
    return result.stdout.strip()


def assert_idle() -> None:
    """Reject deployment while systemd is starting, running or stopping a crawl."""
    state = unit_state(SERVICE)
    if state in {"active", "activating", "deactivating", "reloading"}:
        raise RuntimeError(
            f"Crawler service is {state}; wait for it to finish before deploying"
        )


def assert_no_crawler_containers(compose: list[str]) -> None:
    """Also detect crawls launched manually outside the locked systemd runner."""
    # Config output contains secrets: parse it privately and never print it.
    result = run([*compose, "config", "--format", "json"], capture_output=True)
    project_name = json.loads(result.stdout)["name"]
    containers = run(
        [
            "docker",
            "ps",
            "--filter",
            f"label=com.docker.compose.project={project_name}",
            "--format",
            '{{.Label "com.docker.compose.service"}}',
        ],
        capture_output=True,
    )
    crawler_services = {
        "crawler-init",
        "suumo-links",
        "suumo-html",
        "suumo-page",
        "suumo-tools",
        "suumo-rerun-html",
        "vpn",
        "telegram-test",
    }
    active = crawler_services.intersection(containers.stdout.splitlines())
    if active:
        raise RuntimeError(
            f"Crawler containers are still running: {', '.join(sorted(active))}"
        )


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    """Replace one managed file atomically, preserving restrictive secret permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".release-new")
    temporary.write_bytes(data)
    temporary.chmod(mode)
    os.replace(temporary, path)


def missing_infra_images(compose: list[str]) -> list[str]:
    """Reuse exact configured infra tags already on the host, pulling only missing images."""
    config = json.loads(
        run([*compose, "config", "--format", "json"], capture_output=True).stdout
    )
    missing = []
    for service in ("postgres", "minio"):
        image = config["services"][service]["image"]
        inspected = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if inspected.returncode != 0:
            missing.append(service)
    return missing


def apply_bundle(
    bundle: Path,
    target: Path,
    update_timer: bool = False,
    systemd_directory: Path = Path("/etc/systemd/system"),
    enable_telegram_bot: bool = False,
    enable_ward_dispatch: bool = False,
    catalog_html: Path | None = None,
    enable_vpn_pool: bool = False,
    vpn_archive: Path | None = None,
    container_vpn: bool = False,
) -> None:
    """Validate and pull first, then install with file rollback on command failure."""
    if not (target / ".env").is_file():
        raise ValueError(f"Create the VPS-specific {target / '.env'} before deploying")
    resume_timer = False
    resume_bot = False
    installed = False
    try:
        with (
            release_lock(target),
            tempfile.TemporaryDirectory(prefix="suumo-install-") as temporary,
        ):
            stage = Path(temporary)
            tag = unpack_bundle(bundle, stage)
            # New workers require the VPN namespace. Never install this Compose
            # over a legacy backend without its explicit migration/backup path.
            if (
                not container_vpn
                and read_release_env(target / ".env").get("SUUMO_VPN_BACKEND")
                != "docker"
            ):
                raise ValueError(
                    "This release requires --container-vpn to migrate the host VPN backend"
                )
            env_data = update_tag((target / ".env").read_text(), tag).encode()
            if container_vpn:
                text, count = re.subn(
                    r"(?m)^[ \t]*(?:export[ \t]+)?SUUMO_VPN_BACKEND[ \t]*=.*$",
                    "SUUMO_VPN_BACKEND=docker",
                    env_data.decode(),
                )
                if not count:
                    text = text.rstrip("\n") + "\nSUUMO_VPN_BACKEND=docker\n"
                env_data = text.encode()
            if enable_telegram_bot:
                text = env_data.decode()
                pattern = (
                    r"(?m)^[ \t]*(?:export[ \t]+)?TELEGRAM_CONTROL_ENABLED[ \t]*=.*$"
                )
                text, count = re.subn(pattern, "TELEGRAM_CONTROL_ENABLED=true", text)
                if not count:
                    text = text.rstrip("\n") + "\nTELEGRAM_CONTROL_ENABLED=true\n"
                env_data = text.encode()
            atomic_write(stage / ".env", env_data, 0o600)
            staged_compose = [
                "docker",
                "compose",
                "--project-directory",
                str(target),
                "--env-file",
                str(stage / ".env"),
                "-f",
                str(stage / "docker-compose.release.yml"),
            ]
            assert_idle()
            if unit_state(BOT_SERVICE) in {"active", "activating"}:
                run(["systemctl", "stop", BOT_SERVICE])
                resume_bot = True
            if unit_state(TIMER) == "active":
                run(["systemctl", "stop", TIMER])
                resume_timer = True
            # Recheck after pausing to close the race with an imminent scheduled start.
            assert_idle()
            # Registry failure leaves the release intact; VPN is never changed here.
            assert_no_crawler_containers(staged_compose)
            run(
                [
                    *staged_compose,
                    "pull",
                    "crawler-init",
                    *missing_infra_images(staged_compose),
                ]
            )
            assert_idle()
            assert_no_crawler_containers(staged_compose)
            if enable_ward_dispatch or enable_vpn_pool or container_vpn:
                for unit in (DISPATCH_SERVICE, REFRESH_SERVICE):
                    if unit_state(unit) in {"active", "activating"}:
                        run(["systemctl", "stop", unit])
            install_files(
                stage,
                target,
                tag,
                env_data,
                update_timer or enable_ward_dispatch,
                systemd_directory,
                enable_ward_dispatch,
                catalog_html,
                enable_vpn_pool,
                vpn_archive,
                container_vpn,
            )
            installed = True
    finally:
        # Resume only after releasing the lock, so a due timer can start normally.
        try:
            if installed and enable_telegram_bot:
                run(["systemctl", "enable", "--now", BOT_SERVICE])
            elif resume_bot:
                run(["systemctl", "start", BOT_SERVICE])
        finally:
            if installed and enable_ward_dispatch:
                run(["systemctl", "enable", "--now", TIMER])
            elif resume_timer:
                run(["systemctl", "start", TIMER])


def install_files(
    stage: Path,
    target: Path,
    tag: str,
    env_data: bytes,
    update_timer: bool,
    systemd_directory: Path,
    enable_ward_dispatch: bool = False,
    catalog_html: Path | None = None,
    enable_vpn_pool: bool = False,
    vpn_archive: Path | None = None,
    container_vpn: bool = False,
) -> None:
    """Back up managed files and restore their old versions if infra update fails."""
    files = {target / name: (stage / name).read_bytes() for name in HOST_FILES}
    files[target / ".env"] = env_data
    service_text = (
        (stage / (UNIT_PREFIX + SERVICE))
        .read_text()
        .replace("/opt/suumo-crawler", str(target))
    )
    files[systemd_directory / SERVICE] = service_text.encode()
    files[systemd_directory / BOT_SERVICE] = (
        (stage / (UNIT_PREFIX + BOT_SERVICE))
        .read_text()
        .replace("/opt/suumo-crawler", str(target))
        .encode()
    )
    for unit in (DISPATCH_SERVICE, REFRESH_SERVICE):
        files[systemd_directory / unit] = (
            (stage / (UNIT_PREFIX + unit))
            .read_text()
            .replace("/opt/suumo-crawler", str(target))
            .encode()
        )
    if update_timer or not (systemd_directory / TIMER).exists():
        files[systemd_directory / TIMER] = (stage / (UNIT_PREFIX + TIMER)).read_bytes()
    old_files = {
        path: (path.read_bytes(), path.stat().st_mode & 0o777)
        if path.exists()
        else None
        for path in files
    }
    backup = target / ".releases" / f"{tag}-{uuid.uuid4().hex[:8]}"
    backup.mkdir(parents=True, mode=0o700)
    # Backups include .env secrets and therefore remain private on the VPS.
    for index, (path, previous) in enumerate(old_files.items()):
        if previous is not None:
            atomic_write(backup / str(index), previous[0], 0o600)
    atomic_write(
        backup / "paths.json",
        json.dumps([str(path) for path in files], indent=2).encode(),
        0o600,
    )
    if catalog_html is not None:
        data = catalog_html.read_bytes()
        if len(data) > 2_000_000:
            raise ValueError("Catalogue HTML too large")
        atomic_write(backup / "osaka-city.html", data, 0o600)
        atomic_write(
            backup / "osaka-city.sha256",
            hashlib.sha256(data).hexdigest().encode(),
            0o600,
        )
    host_vpn_state = None
    if container_vpn:
        assert_host_vpn_stopped()
        result = subprocess.run(
            ["systemctl", "is-enabled", "openvpn-client@japan.service"],
            capture_output=True,
            text=True,
        )
        host_vpn_state = result.stdout.strip()
        atomic_write(
            backup / "host-vpn-unit.json",
            json.dumps({"enabled": host_vpn_state}).encode(),
            0o600,
        )
    if enable_ward_dispatch or enable_vpn_pool or container_vpn:
        # Private logical DB + consistent SQLite backups before applying new SQL.
        compose_old = [
            "docker",
            "compose",
            "--env-file",
            str(target / ".env"),
            "-f",
            str(target / "docker-compose.release.yml"),
        ]
        values = read_release_env(target / ".env")
        dump = run(
            [
                *compose_old,
                "exec",
                "-T",
                "postgres",
                "pg_dump",
                "-U",
                values.get("POSTGRES_USER", "suumo_user"),
                "-d",
                values.get("POSTGRES_DB", "suumo_crawler"),
            ],
            capture_output=True,
        )
        atomic_write(backup / "crawler-db.sql", dump.stdout.encode(), 0o600)
        import sqlite3

        db_path = target / "state/telegram-control.sqlite3"
        if db_path.exists():
            with (
                sqlite3.connect(db_path) as source,
                sqlite3.connect(backup / "telegram-control.sqlite3") as destination,
            ):
                source.backup(destination)
            (backup / "telegram-control.sqlite3").chmod(0o600)
        active_config = Path("/etc/openvpn/client/japan.conf")
        if enable_vpn_pool and active_config.exists():
            atomic_write(backup / "japan.conf", active_config.read_bytes(), 0o600)
    try:
        for path, data in files.items():
            atomic_write(path, data, 0o600 if path.name == ".env" else 0o644)
        run(["systemctl", "daemon-reload"])
        compose = [
            "docker",
            "compose",
            "--env-file",
            str(target / ".env"),
            "-f",
            str(target / "docker-compose.release.yml"),
        ]
        # Compose recreates only infra whose configuration changed; volumes are retained.
        run([*compose, "up", "-d", "--pull", "never", "--wait", "postgres", "minio"])
        if enable_ward_dispatch:
            initialize_ward_dispatch(target, compose, catalog_html)
        if enable_vpn_pool:
            initialize_vpn_pool(target, compose, vpn_archive)
        if container_vpn:
            # Disable the old auto-start instance only after files/infra succeed.
            # Never start a VPN or change the host network during installation.
            run(["systemctl", "disable", "openvpn-client@japan.service"])
            run(["systemctl", "mask", "openvpn-client@japan.service"])
            verify_container_vpn(target)
    except Exception:
        if container_vpn and host_vpn_state != "masked":
            subprocess.run(
                ["systemctl", "unmask", "openvpn-client@japan.service"], check=False
            )
            if host_vpn_state == "enabled":
                subprocess.run(
                    ["systemctl", "enable", "openvpn-client@japan.service"], check=False
                )
        for path, previous in old_files.items():
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, previous[0], previous[1])
        subprocess.run(["systemctl", "daemon-reload"], check=False)
        # Best effort restores old infra config; migrations/data are never rolled back.
        if old_files[target / "docker-compose.release.yml"] is not None:
            environment = dict(os.environ)
            environment.pop("SUUMO_CRAWLER_TAG", None)
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "--env-file",
                    str(target / ".env"),
                    "-f",
                    str(target / "docker-compose.release.yml"),
                    "up",
                    "-d",
                    "--pull",
                    "never",
                    "postgres",
                    "minio",
                ],
                check=False,
                env=environment,
            )
        raise
    print(f"Installed image tag {tag}. Backup: {backup}")
    print(
        "Ward catalogue initialized; automatic starts tomorrow at 00:00 Vietnam time."
        if enable_ward_dispatch
        else "Isolated Docker VPN selected; host OpenVPN masked. Queue and schedule preserved."
        if container_vpn
        else "VPN pool initialized; schedule and cooldown preserved."
        if enable_vpn_pool
        else "No migrations or crawler command were run. Existing timer state will be preserved."
    )


def assert_host_vpn_stopped():
    """Refuse migration if any legacy tunnel/process/route is still active."""
    result = run(
        [
            "systemctl",
            "show",
            "openvpn-client@japan.service",
            "--property=ActiveState,MainPID",
        ],
        capture_output=True,
    )
    properties = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    if (
        properties.get("ActiveState") not in {"inactive", "failed"}
        or properties.get("MainPID") != "0"
    ):
        raise RuntimeError("Stop the host VPN before changing backend")
    links = json.loads(run(["ip", "-j", "link", "show"], capture_output=True).stdout)
    if any(r.get("ifname") == "tun0" and "UP" in r.get("flags", []) for r in links):
        raise RuntimeError("Host tunnel is still up")
    for family in ("-4", "-6"):
        routes = json.loads(
            run(
                ["ip", "-j", family, "route", "show", "table", "all"],
                capture_output=True,
            ).stdout
        )
        if any(r.get("dev") == "tun0" for r in routes):
            raise RuntimeError("Host tunnel routes remain")


def verify_container_vpn(target):
    """Validate Docker wiring and internal addresses without starting any VPN or crawl."""
    sys.path.insert(0, str(target / "suumo_source_crawler"))
    sys.path.insert(0, str(target / "suumo_source_crawler/crawler"))
    import scripts

    scripts.__path__.insert(0, str(target / "suumo_source_crawler/scripts"))
    from scripts.telegram_control import Host
    from scripts.docker_vpn import DockerVpn

    controller = DockerVpn(
        Host(
            target / ".env",
            target / "docker-compose.release.yml",
            read_release_env(target / ".env"),
        )
    )
    if not controller.stopped():
        raise RuntimeError("Container VPN is already running")
    for service in ("postgres", "minio"):
        controller.internal_ip(service)
    assert_host_vpn_stopped()


def initialize_vpn_pool(target, compose, archive):
    """Apply only migration 009 and register private configs before resuming dispatcher."""
    if archive is None:
        raise ValueError("VPN initialization requires the separate private archive")
    sys.path.insert(0, str(target / "suumo_source_crawler"))
    sys.path.insert(0, str(target / "suumo_source_crawler/crawler"))
    import scripts

    scripts.__path__.insert(0, str(target / "suumo_source_crawler/scripts"))
    from scripts.telegram_control import Host
    from scripts.vpn_pool import config_dir, receive

    values = read_release_env(target / ".env")
    host = Host(target / ".env", target / "docker-compose.release.yml", values)
    if not host.vpn_stopped():
        raise RuntimeError(
            "VPN is not stopped; initialization refused without changing VPN"
        )
    migration = (
        target / "docker/postgres/migrations/009_crawl_vpn_pool.sql"
    ).read_text()
    run(
        [
            *compose,
            "exec",
            "-T",
            "postgres",
            "psql",
            "-X",
            "-q",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            values.get("POSTGRES_USER", "suumo_user"),
            "-d",
            values.get("POSTGRES_DB", "suumo_crawler"),
        ],
        input=migration,
        capture_output=True,
    )
    with archive.open("rb") as stream:
        print("VPN sync:", receive(host, config_dir(host), stream))


def read_release_env(path):
    # The extracted installer package contains only three files. Do not import
    # the old installed runtime before replacements are installed.
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip().removeprefix("export ")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def initialize_ward_dispatch(target, compose, catalog_html=None):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    sys.path.insert(0, str(target / "suumo_source_crawler"))
    sys.path.insert(0, str(target / "suumo_source_crawler/crawler"))
    import scripts

    scripts.__path__.insert(0, str(target / "suumo_source_crawler/scripts"))
    values = read_release_env(target / ".env")
    migration = (
        target / "docker/postgres/migrations/008_crawl_areas_and_pipeline.sql"
    ).read_text()
    run(
        [
            *compose,
            "exec",
            "-T",
            "postgres",
            "psql",
            "-X",
            "-q",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            values.get("POSTGRES_USER", "suumo_user"),
            "-d",
            values.get("POSTGRES_DB", "suumo_crawler"),
        ],
        input=migration,
        capture_output=True,
    )
    from scripts.telegram_control import Host
    from scripts.telegram_state import state_for
    from scripts.area_catalog import refresh

    host = Host(target / ".env", target / "docker-compose.release.yml", values)
    print(
        "Catalogue:",
        refresh(
            host,
            html=catalog_html.read_text(encoding="utf-8") if catalog_html else None,
        ),
    )
    state = state_for(target / ".env")
    start_at = (
        datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        + timedelta(days=1)
    ).timestamp()
    with state.transaction() as db:
        # Retire old unscoped host summaries while preserving history in backup.
        previous = state.read(db, "pipeline", {})
        if previous and not previous.get("pipeline_key"):
            state.put(db, "pipeline", {})
        pending = state.read(db, "start_request")
        if pending and not pending.get("area"):
            import time

            if 0 <= time.time() - pending["at"] <= 300:
                pending["area"] = next(a for a in host.areas() if a["ward"] == "淀川区")
            else:
                pending = None
            state.put(db, "start_request", pending)
        state.put(db, "automatic_start_at", start_at)
        state.put(db, "next_auto_at", start_at)
    print(
        "Automatic start:",
        datetime.fromtimestamp(start_at, ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(),
    )


def deploy(
    tag: str,
    host: str,
    target: Path,
    apply: bool,
    update_timer: bool,
    enable_telegram_bot: bool = False,
    enable_ward_dispatch: bool = False,
    catalog_html: Path | None = None,
    enable_vpn_pool: bool = False,
    vpn_source: Path = PROJECT_ROOT / "vpn_config",
    container_vpn: bool = False,
) -> None:
    """Show a local-only plan by default; SSH/scp run only with --apply."""
    validate_tag(tag)
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.@-]*", host):
        raise ValueError("Use an SSH config alias, e.g. suumo-vps or user@host")
    print(f"Host: {host}; directory: {target}; image tag: {tag}")
    print("Host bundle:")
    for name in HOST_FILES:
        print(f"  {name}")
    print(
        "Plan: require idle crawler, pause active timer, validate Compose, pull images,"
    )
    print(
        "      back up managed files, install, reload systemd, apply infra, restore timer state."
    )
    print(
        "Preserve: .env values except image tag (and explicit bot enable), tmp, state/ SQLite, VPN config, Docker volumes."
    )
    print(
        "Telegram bot:",
        "enable explicitly"
        if enable_telegram_bot
        else "preserve current state; disabled by default",
    )
    print(
        "Timer schedule:",
        "replace with versioned template"
        if update_timer or enable_ward_dispatch
        else "keep existing schedule",
    )
    if container_vpn:
        print(
            "VPN: switch to Docker, back up DB/state and disable/mask legacy host auto-start; no VPN/crawl during install."
        )
    if catalog_html:
        print(
            "Initial catalogue HTML SHA-256:",
            hashlib.sha256(catalog_html.read_bytes()).hexdigest(),
        )
    if not apply:
        print(
            "DRY RUN: no SSH, scp, Docker or systemctl commands were executed. Add --apply to deploy."
        )
        return
    remote_directory = f"/tmp/suumo-release-{uuid.uuid4().hex}"
    with tempfile.TemporaryDirectory(prefix="suumo-package-") as temporary:
        bundle = build_bundle(tag, Path(temporary) / "release.tar.gz")
        run(["ssh", host, shlex.join(["mkdir", "-m", "700", remote_directory])])
        run(["scp", str(bundle), f"{host}:{remote_directory}/release.tar.gz"])
        if enable_vpn_pool:
            from scripts.vpn_pool import inventory

            rows = inventory(vpn_source)
            if not rows:
                raise ValueError("VPN source is empty")
            private = Path(temporary) / "vpn-private.tar"
            with tarfile.open(private, "w") as archive:
                for row in rows:
                    data = (vpn_source / row["filename"]).read_bytes()
                    if hashlib.sha256(data).hexdigest() != row["sha256"]:
                        raise ValueError("VPN file changed while packaging")
                    info = tarfile.TarInfo(row["filename"])
                    info.size, info.mode = len(data), 0o600
                    archive.addfile(info, io.BytesIO(data))
            private.chmod(0o600)
            run(["scp", str(private), f"{host}:{remote_directory}/vpn-private.tar"])
        if catalog_html:
            run(
                ["scp", str(catalog_html), f"{host}:{remote_directory}/osaka-city.html"]
            )
        installer = "suumo_source_crawler/scripts/deploy_release.py"
        lock_file = "suumo_source_crawler/scripts/runtime_lock.py"
        extract = shlex.join(
            [
                "tar",
                "-xzf",
                remote_directory + "/release.tar.gz",
                "-C",
                remote_directory,
                installer,
                lock_file,
                "suumo_source_crawler/scripts/__init__.py",
            ]
        )
        command = [
            "python3",
            remote_directory + "/" + installer,
            "install",
            "--bundle",
            remote_directory + "/release.tar.gz",
            "--target",
            str(target),
            "--apply",
        ]
        if update_timer:
            command.append("--update-timer")
        if enable_telegram_bot:
            command.append("--enable-telegram-bot")
        if enable_ward_dispatch:
            command.append("--enable-ward-dispatch")
        if container_vpn:
            command.append("--container-vpn")
        if enable_vpn_pool:
            command.extend(
                [
                    "--enable-vpn-pool",
                    "--vpn-archive",
                    remote_directory + "/vpn-private.tar",
                    "--vpn-sha256",
                    hashlib.sha256(private.read_bytes()).hexdigest(),
                ]
            )
        if catalog_html:
            command.extend(
                [
                    "--catalog-html",
                    remote_directory + "/osaka-city.html",
                    "--catalog-sha256",
                    hashlib.sha256(catalog_html.read_bytes()).hexdigest(),
                ]
            )
        run(["ssh", host, extract + " && " + shlex.join(command)])
    print(f"Uploaded bundle retained at {remote_directory} for inspection.")


def main() -> int:
    """Expose package, dry-run deploy and remote-only install commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    package = commands.add_parser(
        "package", help="Create a host bundle locally, without Docker or SSH"
    )
    package.add_argument("--tag", required=True)
    package.add_argument("--output", type=Path, required=True)
    deployment = commands.add_parser(
        "deploy", help="Print a plan; --apply is required for SSH"
    )
    deployment.add_argument("--tag", required=True)
    deployment.add_argument(
        "--host", required=True, help="SSH config alias with user/key/port configured"
    )
    deployment.add_argument("--target", default="/opt/suumo-crawler")
    deployment.add_argument("--apply", action="store_true")
    deployment.add_argument("--update-timer", action="store_true")
    deployment.add_argument("--enable-telegram-bot", action="store_true")
    install = commands.add_parser(
        "install", help="Installer invoked on the VPS by deploy --apply"
    )
    install.add_argument("--bundle", required=True, type=Path)
    install.add_argument("--target", default="/opt/suumo-crawler")
    install.add_argument("--apply", action="store_true")
    install.add_argument("--update-timer", action="store_true")
    install.add_argument("--enable-telegram-bot", action="store_true")
    deployment.add_argument("--enable-ward-dispatch", action="store_true")
    install.add_argument("--enable-ward-dispatch", action="store_true")
    deployment.add_argument("--enable-vpn-pool", action="store_true")
    deployment.add_argument(
        "--vpn-source", type=Path, default=PROJECT_ROOT / "vpn_config"
    )
    install.add_argument("--enable-vpn-pool", action="store_true")
    install.add_argument("--vpn-archive", type=Path)
    install.add_argument("--vpn-sha256")
    deployment.add_argument("--container-vpn", action="store_true")
    install.add_argument("--container-vpn", action="store_true")
    deployment.add_argument(
        "--catalog-html",
        type=Path,
        help="Fresh SUUMO HTML downloaded locally when VPS IP is blocked",
    )
    install.add_argument("--catalog-html", type=Path)
    install.add_argument("--catalog-sha256")
    args = parser.parse_args()
    try:
        if args.command == "package":
            print(build_bundle(args.tag, args.output))
        elif args.command == "deploy":
            deploy(
                args.tag,
                args.host,
                validate_target(args.target),
                args.apply,
                args.update_timer,
                args.enable_telegram_bot,
                args.enable_ward_dispatch,
                args.catalog_html,
                args.enable_vpn_pool,
                args.vpn_source,
                args.container_vpn,
            )
        else:
            if not args.apply:
                raise ValueError("Remote installation requires --apply")
            if args.catalog_html:
                actual = hashlib.sha256(args.catalog_html.read_bytes()).hexdigest()
                if not args.catalog_sha256 or actual != args.catalog_sha256:
                    raise ValueError("Catalogue HTML checksum mismatch")
            if args.enable_vpn_pool and (
                not args.vpn_archive
                or not args.vpn_sha256
                or hashlib.sha256(args.vpn_archive.read_bytes()).hexdigest()
                != args.vpn_sha256
            ):
                raise ValueError("Private VPN archive checksum mismatch")
            apply_bundle(
                args.bundle,
                validate_target(args.target),
                args.update_timer,
                enable_telegram_bot=args.enable_telegram_bot,
                enable_ward_dispatch=args.enable_ward_dispatch,
                catalog_html=args.catalog_html,
                enable_vpn_pool=args.enable_vpn_pool,
                vpn_archive=args.vpn_archive,
                container_vpn=args.container_vpn,
            )
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
        tarfile.TarError,
    ) as exc:
        print(f"Release failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
