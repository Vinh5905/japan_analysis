#!/usr/bin/env python3
"""Single durable dispatcher for the minute timer and confirmed Telegram queue."""
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'crawler'))
from scripts.area_catalog import ward_url, literal, refresh
from scripts.runtime_lock import release_lock
from scripts.telegram_state import state_for
from scripts.run_release_pipeline import read_env_file
from crawler.telegram_notifier import TelegramNotifier, build_event_message
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Asia/Ho_Chi_Minh')
TARGET, MAX_RUNS, REST_SECONDS = 10000, 5, 3600
DISPATCH_SERVICE = 'suumo-crawler-dispatch.service'


def day(now):
    return datetime.fromtimestamp(now, ZONE).date().isoformat()


def decision(state, daily, now):
    start = state.get('automatic_start_at')
    if start is None:
        return 'Lịch chưa được khởi tạo', None
    if now < start:
        return 'Chờ ngày bắt đầu lịch mới', start
    if daily['runs'] >= MAX_RUNS or daily['total_urls'] >= TARGET:
        next_day = datetime.fromtimestamp(now, ZONE).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return ('Đã dùng 5 lượt' if daily['runs'] >= MAX_RUNS else 'Đã đạt 10.000 URL'), next_day.timestamp()
    next_at = max(start, state.get('next_auto_at', start))
    return ('Nghỉ một giờ sau cleanup' if now < next_at else 'Sẵn sàng chạy bù'), next_at


def choose_area(areas):
    # Avoid an empty ward repeated today, then keep lifetime usage balanced.
    return min(areas, key=lambda a: (bool(a['today_runs']), a['runs'], a['last_run'] or '', a['sc']))


def prepare(host, state):
    """Called before any VPN side effect, with a key written before systemctl start."""
    run = state.get('pipeline', {})
    if run.get('status') != 'launching':
        raise RuntimeError('Only dispatcher launches may enter preflight')
    area, key = run['area'], run['pipeline_key']
    result = host.query(f"""INSERT INTO crawl_runs(source_id,area_id,pipeline_key,search_url,area_snapshot,created_by,pipeline_status)
       VALUES({host.source_id},{int(area['area_id'])},{literal(key)},{literal(area['search_url'])},
       {literal(__import__('json').dumps(area))}::jsonb,{literal(run['source'])},'running')
       ON CONFLICT(pipeline_key) DO UPDATE SET pipeline_key=excluded.pipeline_key
       RETURNING json_build_object('run_id',run_id,'created_at',extract(epoch from created_at),
        'status',pipeline_status,'source_id',source_id)""")
    if result['status'] != 'running' or result['source_id'] != host.source_id:
        raise RuntimeError('Pipeline key already finished; refusing replay')
    return state.begin(run_id=result['run_id'], created_at=float(result['created_at']))


def persist_finish(host, state, success, stopped):
    run = state.get('pipeline', {})
    if not run.get('run_id'):
        return  # No DB run was created, so no VPN preflight was permitted.
    status = ('cleanup_failed' if not stopped else 'completed' if success else
              'preflight_failed' if run.get('failure_step') == 'vpn_preflight_failed' else 'crawl_failed')
    now = time.time()
    host.query(f"""WITH interrupted_attempts AS (
      UPDATE crawl_vpn_attempts SET status='interrupted',finished_at=now()
      WHERE run_id={int(run['run_id'])} AND status='pending')
      UPDATE crawl_runs SET pipeline_status={literal(status)},
      pipeline_finished_at=now(), cleanup_confirmed_at={'now()' if stopped else 'NULL'}
      WHERE run_id={int(run['run_id'])} AND pipeline_key={literal(run['pipeline_key'])}
      RETURNING json_build_object('run_id',run_id)""")
    with state.transaction() as db:
        current = state.read(db, 'pipeline', {})
        current.update(status='completed' if success else 'failed', step='completed' if success else status,
                       cleanup_confirmed=stopped, cleanup_finished=now, completion=None)
        state.put(db, 'pipeline', current)
        if stopped:
            state.put(db, 'next_auto_at', now + REST_SECONDS)


def dispatch(host, state, now=None, notifier=None):
    now = time.time() if now is None else now
    with release_lock(host.env_file.parent):
        if host.busy():
            return 'Lượt hiện tại đang chạy hoặc cleanup'
        # DB availability is mandatory even for manual work. Reconcile DB first
        # so loss/stale SQLite can never silently repeat a run.
        unresolved = host.unresolved()
        run = state.get('pipeline', {})
        if unresolved:
            # A host crash can skip ExecStopPost. Recover only after three
            # distinct minute ticks confirm process, tunnel and routes absent.
            if host.vpn_stopped():
                observation = state.get('recovery_observation', {})
                if observation.get('key') != unresolved['pipeline_key']:
                    observation = {'key': unresolved['pipeline_key'], 'checks': 0, 'at': 0}
                if now - observation['at'] >= 30:
                    observation.update(checks=observation['checks']+1, at=now)
                state.set('recovery_observation', observation)
                if observation['checks'] >= 3:
                    recovered = host.query(f"""WITH interrupted_attempts AS (
                      UPDATE crawl_vpn_attempts SET status='interrupted',finished_at=now()
                      WHERE run_id={int(unresolved['run_id'])} AND status='pending')
                      UPDATE crawl_runs SET pipeline_status=CASE
                      WHEN pipeline_status='running' THEN 'interrupted' ELSE pipeline_status END,
                      pipeline_finished_at=coalesce(pipeline_finished_at,now()),cleanup_confirmed_at=now()
                      WHERE run_id={int(unresolved['run_id'])} AND cleanup_confirmed_at IS NULL
                      RETURNING json_build_object('cleanup_epoch',extract(epoch from cleanup_confirmed_at))""")
                    if recovered:
                        with state.transaction() as db:
                            state.put(db,'next_auto_at',float(recovered['cleanup_epoch'])+REST_SECONDS)
                            state.put(db,'pipeline',{'run_id':str(unresolved['run_id']), 'pipeline_key':unresolved['pipeline_key'],
                                'source':unresolved['created_by'],'started':float(unresolved['started']),
                                'area':unresolved['area_snapshot'],'vpn':unresolved.get('vpn_snapshot') or {},'status':'failed','step':'interrupted',
                                'cleanup_confirmed':True,'completion':None})
                            pending = state.read(db,'start_request')
                            if pending and pending['id'] == unresolved['pipeline_key']:
                                state.put(db,'start_request',None)
                        return 'Đã xác nhận cleanup sau restart; khôi phục thời gian nghỉ'
            else:
                state.set('recovery_observation', {})
            state.set('dispatch_reason', 'Cleanup chưa được xác nhận; cần phục hồi lượt ' + str(unresolved['run_id']))
            return state.get('dispatch_reason')
        if run.get('status') == 'launching':
            existing = host.pipeline_by_key(run['pipeline_key'])
            if existing:
                # A completed cleanup persisted in DB before SQLite crashed.
                if not existing.get('cleanup_confirmed_at'):
                    return 'Cleanup chưa được xác nhận'
                state.set('next_auto_at', existing['cleanup_epoch'] + REST_SECONDS)
                state.progress('completed', status='completed', cleanup_confirmed=True)
                pending = state.get('start_request')
                if pending and pending['id'] == run['pipeline_key']:
                    state.set('start_request', None)
            else:
                # Crash between intent write and systemctl: retry same key.
                host.start()
                return 'Phục hồi khởi động đã tiếp nhận'
        elif run.get('run_id'):
            existing = host.pipeline_by_key(run['pipeline_key'])
            if existing and existing.get('cleanup_confirmed_at'):
                state.set('next_auto_at', existing['cleanup_epoch'] + REST_SECONDS)
            elif not run.get('cleanup_confirmed'):
                return 'Cleanup chưa được xác nhận'
        refresh(host)  # One successful sync, never download on every tick.
        daily = host.daily(now)
        pending = state.get('start_request')
        reason, next_at = decision(state, daily, now)
        if not pending:
            state.set('dispatch_reason', reason)
            if daily['runs'] >= MAX_RUNS and daily['total_urls'] < TARGET and state.get('shortfall_day') != day(now):
                # Persist before notifying, avoid duplicate alerts on restart.
                state.set('shortfall_day', day(now))
                if notifier:
                    notifier.send_message(build_event_message('LỊCH NGHỈ ĐẾN NGÀY MỚI', {
                        'Lượt hôm nay': daily['runs'], 'URL còn thiếu': TARGET-daily['total_urls']}))
            if next_at is None or now < next_at or daily['runs'] >= MAX_RUNS or daily['total_urls'] >= TARGET:
                return reason
        areas = host.areas(now)
        if pending:
            matches = [a for a in areas if a['area_id'] == pending['area']['area_id']]
            if not matches:
                raise RuntimeError('Queued ward is unavailable; queue retained')
            area = matches[0]
        else:
            area = choose_area(areas)
        area = {**area, 'search_url': ward_url(host.values.get('SUUMO_SEARCH_URL', ''), area['sc'])}
        state.launch(area, 'manual' if pending else 'schedule', pending['id'] if pending else None, now)
        # An exception leaves the intent recoverable; never remove the queue here.
        host.start()
        state.set('dispatch_reason', 'Đã tiếp nhận khởi động ' + area['display_name'])
        return state.get('dispatch_reason')


def wake(host):
    host.command(['systemctl', 'start', '--no-block', DISPATCH_SERVICE])


def main():
    from scripts.telegram_control import Host
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--compose-file', type=Path, required=True)
    args = parser.parse_args()
    values = read_env_file(args.env_file)
    state = state_for(args.env_file)
    try:
        print(dispatch(Host(args.env_file, args.compose_file, values), state,
                       notifier=TelegramNotifier.from_env(values)))
    except (OSError, RuntimeError, ValueError) as exc:
        state.set('dispatch_reason', 'Chưa khởi động: ' + type(exc).__name__)
        print(type(exc).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
