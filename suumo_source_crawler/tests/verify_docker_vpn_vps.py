"""Run on VPS: staged/live Docker VPN acceptance without crawling or production writes."""
import argparse
from contextlib import contextmanager
import hashlib
import ipaddress
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
import uuid

ROOT = Path('/opt/suumo-crawler')


def command(argv, timeout=30):
    """Never echo args/output that may contain credentials; return only requested data."""
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'Acceptance command failed: {argv[0]} (exit {result.returncode})')
    return result.stdout.strip()


def routes():
    """Take a stable host routing fingerprint, independent of row ordering."""
    return sorted(json.dumps(r, sort_keys=True) for r in json.loads(command(['ip', '-j', '-4', 'route', 'show', 'table', 'all'])))


def main():
    """Pause controls, test isolated VPN, restore only after confirmed cleanup."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, default=ROOT)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--max-trials', type=int, default=23)
    parser.add_argument('--hold-seconds', type=int, default=90, help='Allow a separate fresh SSH/tunnel probe while VPN is live')
    args = parser.parse_args()
    sys.path[:0] = [str(args.stage / 'suumo_source_crawler'), str(args.stage / 'suumo_source_crawler/crawler')]
    from scripts.telegram_control import Host
    from scripts.run_release_pipeline import read_env_file
    from scripts.runtime_lock import release_lock
    from scripts.docker_vpn import DockerVpn
    from scripts.vpn_pool import inventory, config_dir
    from scripts.deploy_release import assert_host_vpn_stopped
    original = read_env_file(ROOT / '.env')
    host = Host(ROOT / '.env', ROOT / 'docker-compose.release.yml', original)
    before_totals = host.total()
    before_stats = host.query('SELECT coalesce(json_agg(v ORDER BY vpn_id),\'[]\'::json) FROM crawl_vpns v')
    state_path = ROOT / 'state/telegram-control.sqlite3'
    import sqlite3
    def schedule():
        """Read only dispatch inputs, avoiding unrelated bot offset changes."""
        with sqlite3.connect('file:' + str(state_path) + '?mode=ro', uri=True) as db:
            return dict(db.execute("SELECT key,value FROM values_store WHERE key IN ('automatic_start_at','next_auto_at','start_request','pipeline')"))
    before_schedule = schedule()
    before_routes = routes()
    with urlopen('https://api.ipify.org', timeout=10) as response:
        host_ip = str(ipaddress.ip_address(response.read().decode().strip()))
    qadir = ROOT / 'tmp' / ('docker-vpn-qa-' + uuid.uuid4().hex[:10])
    qadir.mkdir(mode=0o700, parents=True)
    env = qadir / '.env'
    env.write_text((ROOT / '.env').read_text().rstrip() + '\nSUUMO_CRAWLER_TAG=' + args.tag + '\nSUUMO_VPN_BACKEND=docker\nVPN_RUNTIME_DIR=' + str(qadir / 'runtime') + '\nCRAWLER_TMP_DIR=' + str(qadir / 'tmp') + '\n')
    env.chmod(0o600)
    qa_values = read_env_file(env)
    qa_host = Host(env, args.stage / 'docker-compose.release.yml', qa_values)
    controller = DockerVpn(qa_host)
    worker = None
    paused = []
    clean = False
    owns_vpn = False
    report = {'tag': args.tag, 'host_ip': host_ip, 'trials': [], 'production_totals': before_totals}
    @contextmanager
    def guard():
        """Resume prior controls after the lock is released, including failed QA with clean shutdown."""
        try:
            with release_lock(ROOT):
                yield
        finally:
            if clean:
                for unit in paused:
                    command(['systemctl', 'start', unit])
    with guard():
        try:
            if host.busy() or host.unresolved():
                raise RuntimeError('Crawler/cleanup is not idle')
            assert_host_vpn_stopped()
            if not controller.stopped():
                raise RuntimeError('Existing Docker VPN is running')
            for unit in ('suumo-crawler-pipeline.timer', 'suumo-crawler-telegram.service'):
                if command(['systemctl', 'show', unit, '--property=ActiveState', '--value']) == 'active':
                    command(['systemctl', 'stop', unit])
                    paused.append(unit)
            owns_vpn = True
            for profile in inventory(config_dir(host))[:args.max_trials]:
                print('QA VPN trial: ' + profile['filename'], flush=True)
                if not controller.stop():
                    raise RuntimeError('QA VPN cleanup not confirmed')
                data = (config_dir(host) / profile['filename']).read_bytes()
                controller.prepare(data, profile['filename'])
                controller.start()
                deadline = time.monotonic() + 60
                consecutive = 0
                while time.monotonic() < deadline:
                    try:
                        healthy, reason = controller.health(timeout=min(5, max(0.1, deadline-time.monotonic())))
                    except (OSError, RuntimeError, subprocess.SubprocessError):
                        healthy = False
                    consecutive = consecutive + 1 if healthy else 0
                    if consecutive >= 3:
                        break
                    time.sleep(min(2, max(0, deadline-time.monotonic())))
                report['trials'].append({'filename': profile['filename'], 'healthy': consecutive >= 3})
                if consecutive >= 3:
                    report['filename'] = profile['filename']
                    break
            else:
                raise RuntimeError('No supplied VPN became healthy during QA')
            worker = command([*qa_host.compose, 'run', '-d', '--no-deps', '--entrypoint', 'python', 'suumo-links', '-c', 'import time;time.sleep(600)'])
            vpn = controller.ids()[0]
            namespace = "import os;print(os.readlink('/proc/self/ns/net'))"
            assert command(['docker', 'exec', vpn, 'python', '-c', namespace]) == command(['docker', 'exec', worker, 'python', '-c', namespace])
            probe = """import os,json,ipaddress,urllib.request,psycopg
from minio import Minio
with urllib.request.urlopen('https://api.ipify.org',timeout=15) as r: public_ip=str(ipaddress.ip_address(r.read().decode().strip()))
with psycopg.connect(host='postgres',user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],dbname=os.environ['POSTGRES_DB']) as c:
 totals=c.execute('SELECT count(*),coalesce(sum(total_urls),0) FROM crawl_runs').fetchone()
m=Minio('minio:9000',access_key=os.environ['MINIO_ROOT_USER'],secret_key=os.environ['MINIO_ROOT_PASSWORD'],secure=False)
obj=next(o for o in m.list_objects('suumo',recursive=True) if o.size)
r=m.get_object('suumo',obj.object_name);assert r.read(64);r.close();r.release_conn()
print(json.dumps({'public_ip':public_ip,'db_runs':totals[0],'db_urls':totals[1],'minio_read':True,'dns':open('/etc/resolv.conf').read().splitlines()}))
"""
            result = json.loads(command(['docker', 'exec', worker, 'python', '-c', probe]))
            assert result['public_ip'] != host_ip, 'VPN worker has the host public IP'
            assert result['db_runs'] == before_totals['runs'] and result['db_urls'] == before_totals['total_urls']
            assert routes() == before_routes
            report.update(result)
            print('VPN_ACTIVE ' + json.dumps({'qadir': str(qadir), 'vpn_ip': result['public_ip'], 'host_ip': host_ip, 'minio_read': True, 'postgres_read': True}), flush=True)
            # A separate fresh SSH connection can acknowledge its tunnel check early.
            deadline = time.monotonic() + args.hold_seconds
            while time.monotonic() < deadline and not (qadir / 'ssh-probe-ok').exists():
                time.sleep(1)
            report['fresh_ssh_tunnel_probe'] = (qadir / 'ssh-probe-ok').exists()
            assert report['fresh_ssh_tunnel_probe'], 'Fresh SSH/tunnel acceptance was not acknowledged'
            # Remove the transport while a worker holds its namespace: Internet must fail.
            assert controller.stop()
            blocked = """import socket
s=socket.socket();s.settimeout(3)
try:s.connect(('1.1.1.1',443))
except OSError:print('blocked')
else:raise AssertionError('direct egress survived VPN removal')
finally:s.close()
"""
            assert command(['docker', 'exec', worker, 'python', '-c', blocked]) == 'blocked'
            report['sidecar_removal_blocks_direct_egress'] = True
            assert routes() == before_routes
            assert host.total() == before_totals and host.query('SELECT coalesce(json_agg(v ORDER BY vpn_id),\'[]\'::json) FROM crawl_vpns v') == before_stats
            assert schedule() == before_schedule
            report['host_routes_and_production_state_unchanged'] = True
        finally:
            if worker:
                command(['docker', 'stop', '--time', '5', worker])
                command(['docker', 'rm', worker])
            stopped = not owns_vpn or (controller.stop() and controller.stopped())
            if owns_vpn:
                assert_host_vpn_stopped()
            clean = stopped
            if clean:
                # Only files created in this private QA directory are removed.
                env.unlink(missing_ok=True)
                for name in ('config.ovpn', 'context.json', 'hosts', 'resolv.conf'):
                    (qadir / 'runtime' / name).unlink(missing_ok=True)
                (qadir / 'result.json').write_text(json.dumps(report, indent=2))
            else:
                raise RuntimeError('QA cleanup unconfirmed; controls stay paused')
    print('VPN QA complete: ' + json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
