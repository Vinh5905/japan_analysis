#!/usr/bin/env python3
"""Portable VPN catalogue, append-only SSH upload and bounded preflight rotation."""
from contextlib import contextmanager, ExitStack
import argparse
import fcntl
import hashlib
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'crawler'))
from scripts.area_catalog import literal


def profile(data, filename):
    """Validate self-contained configs without exposing private inline material."""
    if not re.fullmatch(r'[A-Za-z0-9_.-]+\.ovpn', filename) or len(data) > 200_000:
        raise ValueError('Invalid VPN filename or size')
    raw = data.decode('utf-8')
    # Uploaded profiles are data, never an opportunity to run hooks on the host.
    blocks = re.findall(r'<(ca|cert|key)>.*?</\1>', raw, re.S)
    if sorted(blocks) != ['ca', 'cert', 'key']:
        raise ValueError('VPN requires exactly one inline ca/cert/key')
    lines = re.sub(r'<(ca|cert|key)>.*?</\1>', '', raw, flags=re.S)
    allowed = {'client','dev','proto','remote','cipher','data-ciphers','auth',
               'resolv-retry','nobind','persist-key','persist-tun','verb',
               'remote-cert-tls','verify-x509-name','tls-version-min',
               'redirect-gateway','route','auth-nocache','connect-retry','connect-timeout'}
    directives = {}
    for line in lines.splitlines():
        words = shlex.split(line, comments=True)
        if not words or words[0].startswith(';'):
            continue
        if words[0] not in allowed:
            raise ValueError('Unsupported VPN directive: ' + words[0])
        directives.setdefault(words[0], []).append(words[1:])
    if len(directives.get('remote', [])) != 1 or directives.get('dev') not in [[['tun']], [['tun0']]]:
        raise ValueError('VPN needs one remote and tun interface')
    remote = directives['remote'][0]
    ipaddress.IPv4Address(remote[0])
    if len(remote) != 2 or not 1 <= int(remote[1]) <= 65535:
        raise ValueError('Invalid VPN remote port')
    if directives.get('proto') not in [[['tcp']], [['tcp-client']], [['udp']]]:
        raise ValueError('Unsupported VPN transport')
    return {'filename': filename, 'relative_path': filename,
            'sha256': hashlib.sha256(data).hexdigest()}


def config_dir(host):
    """Resolve a machine-specific root while DB paths remain portable."""
    path = Path(host.values.get('VPN_CONFIG_DIR') or host.env_file.parent / 'vpn_config')
    return path if path.is_absolute() else host.env_file.parent / path


def inventory(directory):
    """Return safe file metadata only; refuse symlink configs."""
    rows = []
    if directory.is_symlink():
        raise ValueError('VPN directory cannot be a symlink')
    for path in sorted(directory.glob('*.ovpn')):
        if path.is_symlink() or not path.is_file():
            raise ValueError('VPN profile must be a regular file')
        rows.append(profile(path.read_bytes(), path.name))
    return rows


@contextmanager
def sync_lock(root):
    """Serialize remote uploads and registration through one persistent lock."""
    state = root / 'state'
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'vpn-sync.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def register(host, rows):
    """Reconcile remote files with DB without replacing identities or counters."""
    if not rows:
        return 0
    values = ','.join(f"({literal(r['filename'])},{literal(r['relative_path'])},{literal(r['sha256'])})" for r in rows)
    result = host.query(f"""WITH added AS (
      INSERT INTO crawl_vpns(filename,relative_path,sha256) VALUES {values}
      ON CONFLICT(filename) DO NOTHING RETURNING vpn_id)
      SELECT json_build_object('registered',count(*)) FROM added""")
    # An existing name with changed remote content is never silently re-identified.
    known = host.query("SELECT coalesce(json_agg(v),'[]'::json) FROM (SELECT filename,sha256 FROM crawl_vpns) v")
    hashes = {r['filename']: r['sha256'] for r in known}
    if any(hashes[r['filename']] != r['sha256'] for r in rows):
        raise ValueError('Remote VPN changed under an existing identity; restore original file')
    return result['registered']


def remember_ssh(root):
    """Persist admin IPv4 peers for route bypass when no SSH_CLIENT is inherited."""
    peers = set()
    target = root / 'state/vpn-ssh-bypass.json'
    if target.exists():
        peers.update(json.loads(target.read_text()))
    client = os.environ.get('SSH_CLIENT', '').split()
    if client:
        address = ipaddress.ip_address(client[0])
        if address.version == 4:
            peers.add(str(address))  # IPv6 SSH is unaffected by IPv4 def1 routes.
    if peers:
        from scripts.deploy_release import atomic_write
        atomic_write(target, json.dumps(sorted(peers)).encode(), 0o600)


def receive(host, directory, stream):
    """Accept only new files, then repair missing DB rows after partial failures."""
    from scripts.runtime_lock import release_lock
    from scripts.deploy_release import atomic_write
    with sync_lock(host.env_file.parent), ExitStack() as locks:
        # Check DB before creating files, but retry can reconcile a commit outage.
        host.query('SELECT json_build_object(\'count\',count(*)) FROM crawl_vpns')
        if directory.resolve() != config_dir(host).resolve():
            locks.enter_context(release_lock(host.env_file.parent))
            if host.busy() or not host.vpn_stopped():
                raise RuntimeError('Changing VPN root requires an idle crawler and stopped VPN')
            old = {r['filename']: r['sha256'] for r in host.query("SELECT coalesce(json_agg(v),'[]'::json) FROM (SELECT filename,sha256 FROM crawl_vpns) v")}
            # Hold release lock through registration/path update, so no run sees half relocation.
            changing_root = True
        else:
            old, changing_root = {}, False
        if directory.is_symlink():
            raise ValueError('VPN root cannot be a symlink')
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.chmod(0o700)
        uploaded, skipped = 0, 0
        # Streaming tar never extracts paths or links supplied by the client.
        with tarfile.open(fileobj=stream, mode='r|') as archive:
            seen = set()
            for member in archive:
                if not member.isfile() or member.size > 200_000 or member.name in seen:
                    raise ValueError('Invalid VPN upload archive')
                seen.add(member.name)
                data = archive.extractfile(member).read()
                profile(data, member.name)
                destination = directory / member.name
                if destination.exists() or destination.is_symlink():
                    skipped += 1
                    continue
                with tempfile.NamedTemporaryFile(dir=directory, prefix='.incoming-', delete=False) as temporary:
                    temporary.write(data)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                    temporary_path = Path(temporary.name)
                try:
                    temporary_path.chmod(0o600)
                    # link is atomic and refuses overwrite even if another actor creates it.
                    os.link(temporary_path, destination)
                    uploaded += 1
                finally:
                    temporary_path.unlink(missing_ok=True)
        rows = inventory(directory)
        for row in rows:
            (directory / row['filename']).chmod(0o600)
        if changing_root and any({r['filename']: r['sha256'] for r in rows}.get(name) != digest for name, digest in old.items()):
            raise ValueError('Relocated VPN root is incomplete; existing root retained')
        registered = register(host, rows)
        if changing_root:
            text = host.env_file.read_text()
            text, count = re.subn(r'(?m)^VPN_CONFIG_DIR=.*$', 'VPN_CONFIG_DIR=' + shlex.quote(str(directory)), text)
            if not count:
                text = text.rstrip('\n') + '\nVPN_CONFIG_DIR=' + shlex.quote(str(directory)) + '\n'
            atomic_write(host.env_file, text.encode(), 0o600)
        remember_ssh(host.env_file.parent)
        return {'uploaded': uploaded, 'skipped': skipped, 'registered': registered, 'remote_files': len(rows)}


def sync(hostname, source, root, directory=None, dry_run=False):
    """Send only missing basenames over SSH; existing differing files are reported."""
    rows = inventory(source)
    if not rows:
        raise ValueError('No .ovpn files found')
    if hostname.startswith('-'):
        raise ValueError('Invalid SSH host')
    script = str(root / 'suumo_source_crawler/scripts/vpn_pool.py')
    base = ['python3', script, '--env-file', str(root / '.env')]
    if directory:
        base += ['--vpn-dir', str(directory)]
    result = subprocess.run(['ssh', hostname, shlex.join(base + ['inventory'])], check=True, capture_output=True, text=True)
    existing = {r['filename']: r['sha256'] for r in json.loads(result.stdout)}
    new = [r for r in rows if r['filename'] not in existing]
    changed = [r['filename'] for r in rows if r['filename'] in existing and existing[r['filename']] != r['sha256']]
    report = {'new': len(new), 'skipped_existing': len(rows)-len(new), 'different_content_skipped': changed}
    if not dry_run:
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode='w') as archive:
            for row in new:
                data = (source / row['filename']).read_bytes()
                if profile(data, row['filename']) != row:
                    raise ValueError('Local VPN changed during sync')
                info = tarfile.TarInfo(row['filename'])
                info.size, info.mode = len(data), 0o600
                archive.addfile(info, io.BytesIO(data))
        result = subprocess.run(['ssh', hostname, shlex.join(base + ['receive'])], input=payload.getvalue(), check=True, capture_output=True)
        report.update(json.loads(result.stdout))
    return report


def start_attempt(host, run, vpn):
    """Reserve one trial before touching systemd, including failed configuration trials."""
    return host.query(f"""WITH a AS (
      INSERT INTO crawl_vpn_attempts(run_id,vpn_id,snapshot)
      SELECT {int(run['run_id'])},{int(vpn['vpn_id'])},{literal(json.dumps(vpn))}::jsonb
      FROM crawl_runs WHERE run_id={int(run['run_id'])} AND pipeline_status='running'
      ON CONFLICT(run_id,vpn_id) DO NOTHING RETURNING *),
      v AS (UPDATE crawl_vpns SET last_attempt_at=now() WHERE vpn_id IN (SELECT vpn_id FROM a))
      SELECT row_to_json(a) FROM a""")


def finish_attempt(host, attempt, success):
    """Atomically finalize trial counters and freeze the successful run's VPN."""
    vid, rid = int(attempt['vpn_id']), int(attempt['run_id'])
    status = 'success' if success else 'failed'
    return host.query(f"""WITH a AS (
      UPDATE crawl_vpn_attempts SET status={literal(status)},finished_at=now()
      WHERE attempt_id={int(attempt['attempt_id'])} AND status='pending' RETURNING *),
      v AS (UPDATE crawl_vpns SET activation_successes=activation_successes+{int(success)},
       activation_failures=activation_failures+{int(not success)},
       last_used_at=CASE WHEN {literal(status)}='success' THEN now() ELSE last_used_at END
       WHERE vpn_id={vid} AND EXISTS(SELECT 1 FROM a)),
      r AS (UPDATE crawl_runs SET vpn_id={vid},vpn_snapshot=(SELECT snapshot FROM a)
       WHERE run_id={rid} AND {literal(status)}='success' AND EXISTS(SELECT 1 FROM a))
      SELECT row_to_json(a) FROM a""")


def runtime_config(data, peers):
    """Keep inline credentials and normalize tun/redirect routes without script hooks."""
    text = data.decode('utf-8')
    text = re.sub(r'(?m)^\s*(dev|redirect-gateway)\s+[^\n]*$', '', text)
    # Existing profile routes remain; bypasses always use the original gateway.
    return (text.rstrip() + '\ndev tun0\nredirect-gateway def1\n' + ''.join(
        f'route {ipaddress.IPv4Address(peer)} 255.255.255.255 net_gateway\n' for peer in sorted(set(peers)))).encode()


def select_vpn(host, state, service='openvpn-client@japan', interface='tun0', notifier=None,
               runner=None, sleeper=time.sleep, config_target=Path('/etc/openvpn/client/japan.conf'),
               timeout=60, monotonic=time.monotonic):
    """Try oldest-attempt configs once; never proceed without verified shutdown."""
    from scripts.ensure_openvpn import run_command, restart_vpn, vpn_health_reason
    from scripts.stop_openvpn import stop_vpn
    from scripts.telegram_state import install_context
    from scripts.deploy_release import atomic_write
    from crawler.telegram_notifier import build_event_message
    from scripts.docker_vpn import DockerVpn, docker_backend
    runner = runner or run_command
    run = state.get('pipeline', {})
    candidates = host.query("SELECT coalesce(json_agg(v ORDER BY last_attempt_at NULLS FIRST,filename),'[]'::json) FROM crawl_vpns v WHERE enabled")
    if not candidates:
        raise RuntimeError('No registered VPN profiles; run make vpn-sync')
    docker = DockerVpn(host) if docker_backend(host.values) else None
    if docker is not None and not host.vpn_stopped():
        raise RuntimeError('Host or container VPN is still running; preflight blocked')
    peers_path = host.env_file.parent / 'state/vpn-ssh-bypass.json'
    peers = json.loads(peers_path.read_text()) if peers_path.exists() else []
    # Preserve old route bypasses as well as peers persisted by authenticated uploads.
    if config_target.exists():
        for peer in re.findall(r'(?m)^\s*route\s+([0-9.]+)\s+255\.255\.255\.255\s+net_gateway\s*$', config_target.read_text()):
            peers.append(str(ipaddress.IPv4Address(peer)))
    sockets = runner(('ss', '-Htn', 'state', 'established', '( sport = :22 )')) if docker is None else subprocess.CompletedProcess([], 0, '', '')
    if sockets.returncode == 0:
        for line in sockets.stdout.splitlines():
            try:
                peers.append(str(ipaddress.IPv4Address(line.split()[-1].rsplit(':', 1)[0])))
            except (ValueError, IndexError):
                pass
    for vpn in candidates:
        if not (docker.stop(sleeper) if docker else stop_vpn(service, interface, runner=runner, sleeper=sleeper)):
            raise RuntimeError('VPN shutdown unconfirmed; fallback blocked')
        attempt = start_attempt(host, run, vpn)
        if not attempt:
            raise RuntimeError('VPN trial already started; refusing replay')
        state.progress('vpn_preflight', vpn_attempt=vpn)
        install_context(state.get('pipeline'))
        if notifier:
            notifier.send_message(build_event_message('ĐANG THỬ VPN', {'VPN': vpn['filename'], 'Giới hạn': '60 giây'}))
        healthy = False
        try:
            path = config_dir(host) / vpn['relative_path']
            if path.is_symlink():
                raise ValueError('VPN profile cannot be a symlink')
            data = path.read_bytes()
            if profile(data, vpn['filename'])['sha256'] != vpn['sha256']:
                raise ValueError('VPN checksum mismatch')
            if docker:
                docker.prepare(data, vpn['filename'])
            else:
                atomic_write(config_target, runtime_config(data, peers), 0o600)
            deadline = monotonic() + timeout
            def bounded(command):
                """Bound every activation subprocess by the trial's remaining time."""
                remaining = deadline-monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, timeout)
                if runner is run_command:
                    return subprocess.run(list(command), capture_output=True, text=True,
                                          timeout=min(5, remaining), check=False)
                return runner(command)
            if docker:
                docker.start(timeout=max(0.1, deadline-monotonic()))
                started = True
            else:
                started = restart_vpn(service, bounded)
            if started:
                consecutive = 0
                while monotonic() < deadline:
                    ok, _ = docker.health(timeout=max(0.1, min(5, deadline-monotonic()))) if docker else vpn_health_reason(service, interface, bounded)
                    consecutive = consecutive+1 if ok else 0
                    if consecutive >= 3 and monotonic() < deadline:
                        healthy = True
                        break
                    sleeper(min(2, max(0, deadline-monotonic())))
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            # Report only exception type; raw config and command output contain keys.
            print('VPN trial error: ' + type(exc).__name__, flush=True)
        if not finish_attempt(host, attempt, healthy):
            raise RuntimeError('VPN trial could not be finalized; refusing crawl')
        if notifier:
            notifier.send_message(build_event_message('VPN ĐÃ BẬT' if healthy else 'VPN KHÔNG BẬT ĐƯỢC', {'VPN': vpn['filename']}))
        if healthy:
            state.progress('vpn_preflight', vpn=vpn)
            install_context(state.get('pipeline'))
            return True
    # Last failed config must also be stopped before returning.
    if not (docker.stop(sleeper) if docker else stop_vpn(service, interface, runner=runner, sleeper=sleeper)):
        raise RuntimeError('Last VPN shutdown unconfirmed')
    return False


def main():
    """Expose local sync and authenticated host inventory/receive operations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--vpn-dir', type=Path)
    parser.add_argument('--host', default='thuevpsgiare')
    parser.add_argument('--source', type=Path, default=ROOT / 'vpn_config')
    parser.add_argument('--remote-root', type=Path, default=Path('/opt/suumo-crawler'))
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('command', choices=['sync','inventory','receive'])
    args = parser.parse_args()
    try:
        if args.command == 'sync':
            result = sync(args.host, args.source, args.remote_root, args.vpn_dir, args.dry_run)
        else:
            from scripts.telegram_control import Host
            from scripts.run_release_pipeline import read_env_file
            env = args.env_file.resolve()
            host = Host(env, env.parent / 'docker-compose.release.yml', read_env_file(env))
            directory = args.vpn_dir or config_dir(host)
            if not directory.is_absolute() or any(c in str(directory) for c in '\n\r'):
                raise ValueError('Remote VPN root must be absolute')
            result = inventory(directory) if args.command == 'inventory' else receive(host, directory, sys.stdin.buffer)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print('VPN operation failed: ' + type(exc).__name__ + (': ' + str(exc) if isinstance(exc, (ValueError, RuntimeError)) else ''), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
