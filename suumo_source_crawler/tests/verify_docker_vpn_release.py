"""Read-only release acceptance after deploying the Docker VPN backend."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'suumo_source_crawler'))
from scripts.deploy_release import HOST_FILES
from scripts.vpn_pool import inventory

REMOTE = r'''
import hashlib,json,sqlite3,subprocess,sys,time
from pathlib import Path
EXPECTED
root=Path('/opt/suumo-crawler')
sys.path[:0]=[str(root/'suumo_source_crawler'),str(root/'suumo_source_crawler/crawler')]
from scripts.telegram_control import Host,TelegramApi,COMMANDS
from scripts.run_release_pipeline import read_env_file
from scripts.docker_vpn import DockerVpn
from scripts.vpn_pool import inventory,config_dir
from scripts import telegram_ui as ui
values=read_env_file(root/'.env')
host=Host(root/'.env',root/'docker-compose.release.yml',values)
assert values['SUUMO_CRAWLER_TAG']==expected['tag'] and values['SUUMO_VPN_BACKEND']=='docker'
for name,digest in expected['host_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'host checksum: '+name
assert inventory(config_dir(host))==expected['vpns'],'private VPN inventory changed'
assert config_dir(host).stat().st_mode & 0o777==0o700
assert all((config_dir(host)/r['filename']).stat().st_mode & 0o777==0o600 for r in expected['vpns'])
stats=host.query('SELECT json_agg(v ORDER BY filename) FROM crawl_vpns v')
assert len(stats)==23 and all(v['total_requests']==v['activation_successes']==v['activation_failures']==0 and v['last_attempt_at'] is None and v['last_used_at'] is None for v in stats)
assert all(next(v for v in stats if v['filename']==r['filename'])['sha256']==r['sha256'] for r in expected['vpns'])
assert host.total()=={'total_urls':65551,'runs':39} and len(host.areas())==24
assert host.vpn_stopped() and not host.busy() and not host.unresolved()
controller=DockerVpn(host)
assert controller.stopped()
infra={s:controller.internal_ip(s) for s in ('postgres','minio')}
assert host.command(['systemctl','show','openvpn-client@japan.service','--property=UnitFileState','--value']).strip()=='masked'
with sqlite3.connect('file:'+str(root/'state/telegram-control.sqlite3')+'?mode=ro',uri=True) as db:
    class State:
        def get(self,key,default=None):
            """Read persisted status without touching the bot state."""
            row=db.execute('SELECT value FROM values_store WHERE key=?',(key,)).fetchone()
            return json.loads(row[0]) if row else default
    state=State()
    schedule={k:state.get(k) for k in ('automatic_start_at','next_auto_at','start_request')}
    assert schedule=={'automatic_start_at':1791565200.0,'next_auto_at':1791565200.0,'start_request':None}
    status=host.status(state)
    assert 'Docker' in status['VPN']
    assert len(ui.status(status,time.time())[0].encode('utf-16-le'))//2<=4096
units={name:host.properties(name,['ActiveState','SubState','Result']) for name in ('suumo-crawler-pipeline.service','openvpn-client@japan','suumo-crawler-telegram.service','suumo-crawler-pipeline.timer','suumo-crawler-dispatch.service')}
assert units['suumo-crawler-telegram.service']['ActiveState']=='active'
assert units['suumo-crawler-pipeline.timer']['ActiveState']=='active'
assert units['suumo-crawler-dispatch.service'].get('Result')=='success'
menu=TelegramApi(values['TELEGRAM_BOT_TOKEN']).call('getMyCommands',{'scope':{'type':'chat','chat_id':values['TELEGRAM_CHAT_ID']}})
assert [c['command'] for c in menu]==[k for k,_ in COMMANDS]
unit=Path('/etc/systemd/system/suumo-crawler-pipeline.service').read_text()
assert 'ExecStartPre=' in unit and 'ensure_openvpn.py' in unit and 'ExecStopPost=' in unit and 'stop_openvpn.py' in unit
assert '--compose-file /opt/suumo-crawler/docker-compose.release.yml' in unit
assert 'Wants=openvpn' not in unit and 'Requires=openvpn' not in unit
subprocess.run(['systemd-analyze','verify','/etc/systemd/system/suumo-crawler-pipeline.service'],capture_output=True,text=True,check=True,timeout=20)
image=values.get('SUUMO_CRAWLER_IMAGE','kevinpham9257/suumo-crawler')+':'+expected['tag']
digests=json.loads(subprocess.run(['docker','image','inspect',image,'--format','{{json .RepoDigests}}'],capture_output=True,text=True,check=True,timeout=20).stdout)
assert any(d.endswith('@'+expected['digest']) for d in digests)
code='import hashlib,json;from pathlib import Path;print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in ['+','.join('Path('+repr(n)+')' for n in expected['image_files'])+']}));assert not list(Path("/app").rglob("*.ovpn"))'
actual=json.loads(subprocess.run(['docker','run','--rm','--network','none',image,'python','-c',code],capture_output=True,text=True,check=True,timeout=30).stdout)
assert actual==expected['image_files'],'image checksum mismatch'
backup=root/'.releases'/expected['backup']
assert all((backup/name).is_file() for name in ('crawler-db.sql','telegram-control.sqlite3','host-vpn-unit.json','paths.json'))
assert json.loads((backup/'host-vpn-unit.json').read_text())['enabled']=='enabled'
paths=json.loads((backup/'paths.json').read_text());oldenv=read_env_file(backup/str(paths.index(str(root/'.env'))))
assert {k:v for k,v in oldenv.items() if k not in ('SUUMO_CRAWLER_TAG','SUUMO_VPN_BACKEND')}=={k:v for k,v in values.items() if k not in ('SUUMO_CRAWLER_TAG','SUUMO_VPN_BACKEND')}
assert hashlib.sha256(Path('/etc/openvpn/client/japan.conf').read_bytes()).hexdigest()=='c95075bb458f395a8132bf1cc60cafbe04245f352949d4191f138acca423d4ef'
print(json.dumps({'tag':expected['tag'],'host_checksums':len(expected['host_files']),'image_checksums':len(actual),'digest':expected['digest'],'VPNs':len(stats),'history':host.total(),'schedule':schedule,'menu_commands':len(menu),'infra':infra,'units':units,'legacy_host_vpn':'masked/inactive','backup':str(backup),'systemd_unit_valid':True}))
'''


def main():
    """Send checksums and read-only verification through SSH, never raw private profiles."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--digest', required=True)
    parser.add_argument('--backup', required=True)
    args = parser.parse_args()
    image_files = {
        '/app/crawler/' + name: hashlib.sha256((ROOT / 'suumo_source_crawler/crawler' / name).read_bytes()).hexdigest()
        for name in ('crawler/vpn_accounting.py', 'crawler/metadata_db.py', 'crawler/settings.py',
                     'crawler/telegram_extension.py', 'crawler/telegram_notifier.py', 'tools/manual_rerun_failed_html.py')}
    image_files['/app/vpn/container_vpn.py'] = hashlib.sha256((ROOT / 'suumo_source_crawler/vpn/container_vpn.py').read_bytes()).hexdigest()
    expected = {**vars(args), 'host_files': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in HOST_FILES},
                'vpns': inventory(ROOT / 'suumo_source_crawler/vpn_config'), 'image_files': image_files}
    result = subprocess.run(['ssh', 'thuevpsgiare', 'python3 -'], input=REMOTE.replace('EXPECTED', 'expected=json.loads(' + repr(json.dumps(expected)) + ')'), capture_output=True, text=True)
    if result.returncode:
        print(result.stderr)
        return result.returncode
    print(result.stdout)
    (ROOT / 'tmp/releases' / (args.tag + '-verification.json')).write_text(result.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
