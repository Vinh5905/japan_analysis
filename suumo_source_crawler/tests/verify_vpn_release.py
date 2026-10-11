"""Read-only VPS release acceptance; never start a crawl or OpenVPN."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "suumo_source_crawler"))
from scripts.deploy_release import HOST_FILES
from scripts.vpn_pool import inventory

REMOTE = r"""
import hashlib,json,sqlite3,subprocess,sys,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
EXPECTED
root=Path('/opt/suumo-crawler')
sys.path[:0]=[str(root/'suumo_source_crawler'),str(root/'suumo_source_crawler/crawler')]
from scripts.telegram_control import Host,TelegramApi,COMMANDS
from scripts.run_release_pipeline import read_env_file
from scripts.vpn_pool import inventory,config_dir
from scripts import telegram_ui as ui
values=read_env_file(root/'.env')
host=Host(root/'.env',root/'docker-compose.release.yml',values)
assert values['SUUMO_CRAWLER_TAG']==expected['tag'],'tag mismatch'
for name,digest in expected['host_files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'host checksum: '+name
rows=inventory(config_dir(host))
assert rows==expected['vpns'],'VPN inventory/checksum mismatch'
assert config_dir(host).stat().st_mode & 0o777==0o700,'VPN directory permissions'
assert all((config_dir(host)/r['filename']).stat().st_mode & 0o777==0o600 for r in rows),'VPN file permissions'
stats=host.query('SELECT json_agg(v ORDER BY filename) FROM crawl_vpns v')
assert len(stats)==23 and all(v['enabled'] and v['total_requests']==v['activation_successes']==v['activation_failures']==0 and v['last_attempt_at'] is None and v['last_used_at'] is None for v in stats),'initial stats'
assert all(next(v for v in stats if v['filename']==r['filename'])['sha256']==r['sha256'] for r in rows),'DB/file hash mismatch'
assert host.total()=={'total_urls':65551,'runs':39},'historical totals changed'
assert len(host.areas())==24,'ward catalogue changed'
assert host.query("SELECT json_build_object('fn',to_regprocedure('record_crawl_vpn_request(uuid,bigint,bigint,text)') IS NOT NULL)")['fn'],'migration function missing'
assert host.vpn_stopped() and not host.busy(),'crawler/VPN not idle'
with sqlite3.connect('file:'+str(root/'state/telegram-control.sqlite3')+'?mode=ro',uri=True) as db:
    class State:
        def get(self,key,default=None):
            row=db.execute('SELECT value FROM values_store WHERE key=?',(key,)).fetchone()
            return json.loads(row[0]) if row else default
    state=State()
    schedule={k:state.get(k) for k in ('automatic_start_at','next_auto_at','start_request')}
    assert schedule=={'automatic_start_at':1791565200.0,'next_auto_at':1791565200.0,'start_request':None},'schedule/queue changed'
    status_card=ui.status(host.status(state),time.time())[0]
    history_card=ui.history(host.history(),'SUUMO',time.time())[0]
    assert all(len(c.encode('utf-16-le'))//2<=4096 for c in (status_card,history_card)),'Telegram card size'
units={name:host.properties(name,['ActiveState','SubState','Result']) for name in ('suumo-crawler-pipeline.service','openvpn-client@japan','suumo-crawler-telegram.service','suumo-crawler-pipeline.timer','suumo-crawler-dispatch.service')}
assert units['suumo-crawler-telegram.service']['ActiveState']=='active','bot inactive'
assert units['suumo-crawler-pipeline.timer']['ActiveState']=='active','timer inactive'
assert units['suumo-crawler-dispatch.service'].get('Result')=='success','dispatcher failing'
menu=TelegramApi(values['TELEGRAM_BOT_TOKEN']).call('getMyCommands',{'scope':{'type':'chat','chat_id':values['TELEGRAM_CHAT_ID']}})
assert [c['command'] for c in menu]==[k for k,_ in COMMANDS],'Telegram menu mismatch'
image=values.get('SUUMO_CRAWLER_IMAGE','kevinpham9257/suumo-crawler')+':'+expected['tag']
digests=json.loads(subprocess.run(['docker','image','inspect',image,'--format','{{json .RepoDigests}}'],capture_output=True,text=True,check=True,timeout=20).stdout)
assert any(d.endswith('@'+expected['digest']) for d in digests),'image digest mismatch'
code="import hashlib,json;from pathlib import Path;import crawler.vpn_accounting;print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in ["+','.join('Path('+repr(n)+')' for n in expected['image_files'])+"]}));assert not list(Path('/app').rglob('*.ovpn'))"
actual=json.loads(subprocess.run(['docker','run','--rm','--network','none',image,'python','-c',code],capture_output=True,text=True,check=True,timeout=30).stdout)
assert actual==expected['image_files'],'image source checksum mismatch'
config_hash=hashlib.sha256(Path('/etc/openvpn/client/japan.conf').read_bytes()).hexdigest()
assert config_hash=='c95075bb458f395a8132bf1cc60cafbe04245f352949d4191f138acca423d4ef','active config changed during deploy'
backup=root/'.releases/20261009-vpn-03-c9a3878b'
assert all((backup/name).is_file() for name in ('crawler-db.sql','telegram-control.sqlite3','japan.conf','paths.json')),'backup missing'
assert hashlib.sha256((backup/'japan.conf').read_bytes()).hexdigest()==config_hash,'VPN backup mismatch'
print(json.dumps({'tag':expected['tag'],'host_checksums':len(expected['host_files']),'VPNs':len(rows),'initial_requests':0,'history':host.total(),'schedule':schedule,'automatic_start':datetime.fromtimestamp(schedule['automatic_start_at'],ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),'menu_commands':len(menu),'image_digest':expected['digest'],'image_checksums':len(actual),'units':units,'backup':str(backup)}))
"""


def main():
    """Ship only checksum metadata and verification code, never private config data."""
    image_files = {
        "/app/crawler/"
        + str(p.relative_to(ROOT / "suumo_source_crawler/crawler")): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in [
            ROOT / "suumo_source_crawler/crawler" / name
            for name in (
                "crawler/vpn_accounting.py",
                "crawler/metadata_db.py",
                "crawler/settings.py",
                "crawler/telegram_extension.py",
                "crawler/telegram_notifier.py",
                "tools/manual_rerun_failed_html.py",
            )
        ]
    }
    expected = {
        "tag": "20261009-vpn-03",
        "digest": "sha256:21cb803aa1b1dcca4c7cb924b001631c9009278704ea7cc62eadbad78b588a90",
        "host_files": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in HOST_FILES
        },
        "vpns": inventory(ROOT / "suumo_source_crawler/vpn_config"),
        "image_files": image_files,
    }
    code = REMOTE.replace(
        "EXPECTED", "expected=json.loads(" + repr(json.dumps(expected)) + ")"
    )
    result = subprocess.run(
        ["ssh", "thuevpsgiare", shlex.join(["python3", "-"])],
        input=code,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(result.stderr)
        return result.returncode
    print(result.stdout)
    (ROOT / "tmp/releases/vpn-03-verification.json").write_text(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
