"""Offline acceptance for append-only sync, bounded rotation and cleanup gates."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'suumo_source_crawler'))
from scripts import vpn_pool as pool
from scripts.telegram_state import ControlState

DATA = b'client\ndev tun\nproto tcp\nremote 192.0.2.1 443\n<ca>test</ca>\n<cert>test</cert>\n<key>test</key>\n'


def archive(files):
    """Create a private upload stream from test-only inline certificates."""
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as tar:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            tar.addfile(entry, io.BytesIO(data))
    stream.seek(0)
    return stream


class VpnPoolTests(unittest.TestCase):
    def setUp(self):
        """Isolate files and environment; no commands ever reach real OpenVPN."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.env = self.root / '.env'
        self.env.write_text('OTHER=keep\n')
        self.host = Mock(env_file=self.env, values={})
        self.host.query.return_value = {'count': 0}
        self.host.busy.return_value = False
        self.host.vpn_stopped.return_value = True
        self.directory = self.root / 'vpn_config'
        self.directory.mkdir()
        for filename in ('a.ovpn','b.ovpn'):
            (self.directory / filename).write_bytes(DATA)
        self.state = ControlState(self.root / 'state/control.sqlite3')
        self.state.launch({'area_id':1,'display_name':'Yodogawa'}, 'manual')
        self.state.begin(run_id=42, created_at=0)
        self.profiles = [{**r, 'vpn_id':i+1} for i,r in enumerate(pool.inventory(self.directory))]
        env_patch = patch.dict(os.environ, {}, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def test_all_supplied_profiles_validate_without_private_output(self):
        """Validate the actual input inventory without copying secrets into fixtures."""
        rows = pool.inventory(ROOT / 'suumo_source_crawler/vpn_config')
        self.assertEqual(len(rows), 23)
        self.assertTrue(all(set(r) == {'filename','relative_path','sha256'} for r in rows))

    def test_reject_hooks_traversal_external_keys_symlinks(self):
        for name,data in (('../a.ovpn',DATA),('a.ovpn',DATA+b'up /tmp/script\n'),
                          ('a.ovpn',DATA.replace(b'<key>test</key>',b'key /tmp/key'))):
            with self.assertRaises(ValueError): pool.profile(data,name)
        (self.directory / 'link.ovpn').symlink_to(self.directory / 'a.ovpn')
        with self.assertRaises(ValueError): pool.inventory(self.directory)

    @patch.object(pool, 'register', return_value=1)
    def test_sync_never_overwrites_and_registers_actual_remote_file(self, register):
        other = DATA.replace(b'192.0.2.1',b'192.0.2.2')
        result = pool.receive(self.host,self.directory,archive({'a.ovpn':other,'c.ovpn':DATA}))
        self.assertEqual((result['uploaded'],result['skipped'],result['registered']), (1,1,1))
        self.assertEqual((self.directory/'a.ovpn').read_bytes(),DATA)
        rows = register.call_args.args[1]
        self.assertEqual(next(r for r in rows if r['filename']=='a.ovpn')['sha256'],pool.profile(DATA,'a.ovpn')['sha256'])
        self.assertEqual((self.directory/'c.ovpn').stat().st_mode & 0o777,0o600)
        self.assertEqual(self.directory.stat().st_mode & 0o777,0o700)

    def test_partial_db_failure_retry_repairs_registration_without_upload(self):
        with patch.object(pool,'register',side_effect=RuntimeError('DB down')):
            with self.assertRaises(RuntimeError): pool.receive(self.host,self.directory,archive({'c.ovpn':DATA}))
        self.assertTrue((self.directory/'c.ovpn').exists())
        with patch.object(pool,'register',return_value=1) as register:
            result = pool.receive(self.host,self.directory,archive({}))
            self.assertEqual((result['uploaded'],result['registered']), (0,1))
            self.assertEqual(len(register.call_args.args[1]),3)

    def test_db_unavailable_creates_no_new_file(self):
        self.host.query.side_effect = RuntimeError('DB down')
        with self.assertRaises(RuntimeError): pool.receive(self.host,self.directory,archive({'c.ovpn':DATA}))
        self.assertFalse((self.directory/'c.ovpn').exists())

    def test_parallel_sync_is_locked(self):
        with pool.sync_lock(self.root):
            with self.assertRaises(BlockingIOError):
                pool.receive(self.host,self.directory,archive({'c.ovpn':DATA}))
        self.assertFalse((self.directory/'c.ovpn').exists())

    def test_host_database_commands_do_not_drain_incoming_ssh_archive(self):
        """Use real child stdin to catch Compose-style consumption before tar parsing."""
        code=(f"import sys;sys.path.insert(0,{str(ROOT/'suumo_source_crawler')!r});"
              "from scripts.telegram_control import host_command;"
              "host_command([sys.executable,'-c','import sys;sys.stdin.buffer.read()']);"
              "sys.stdout.buffer.write(sys.stdin.buffer.read())")
        result=subprocess.run([sys.executable,'-c',code],input=b'vpn-archive-sentinel',
                              capture_output=True,check=True,timeout=5)
        self.assertEqual(result.stdout,b'vpn-archive-sentinel')

    def test_relocated_root_changes_only_machine_config_and_preserves_relative_paths(self):
        self.host.query.side_effect = [{'count':2},[{'filename':r['filename'],'sha256':r['sha256']} for r in self.profiles]]
        relocated = self.root/'new_machine'
        with patch.object(pool,'register',return_value=0):
            pool.receive(self.host,relocated,archive({'a.ovpn':DATA,'b.ovpn':DATA}))
        self.assertIn('OTHER=keep',self.env.read_text())
        self.assertIn('VPN_CONFIG_DIR='+str(relocated),self.env.read_text())
        self.assertEqual([r['relative_path'] for r in pool.inventory(relocated)],['a.ovpn','b.ovpn'])

    def test_relocation_requires_idle_and_complete_existing_catalog(self):
        self.host.busy.return_value=True
        with self.assertRaises(RuntimeError): pool.receive(self.host,self.root/'other',archive({}))
        self.assertNotIn('VPN_CONFIG_DIR',self.env.read_text())
        self.host.busy.return_value=False
        self.host.query.side_effect=[{'count':2},[{'filename':'missing.ovpn','sha256':'0'*64}]]
        with self.assertRaises(ValueError): pool.receive(self.host,self.root/'other',archive({'a.ovpn':DATA}))
        self.assertNotIn('VPN_CONFIG_DIR',self.env.read_text())

    def test_local_sync_uploads_only_new_names_and_reports_changed_existing(self):
        inventory = [{'filename':'a.ovpn','sha256':'0'*64}]
        results = [subprocess.CompletedProcess([],0,json.dumps(inventory),''),
                   subprocess.CompletedProcess([],0,b'{"uploaded":1,"registered":1}',b'')]
        with patch.object(pool.subprocess,'run',side_effect=results) as run:
            report = pool.sync('vps',self.directory,Path('/opt/test'))
        self.assertEqual(report['different_content_skipped'],['a.ovpn'])
        with tarfile.open(fileobj=io.BytesIO(run.call_args.kwargs['input'])) as tar:
            self.assertEqual(tar.getnames(),['b.ovpn'])
        with patch.object(pool.subprocess,'run',return_value=results[0]) as run:
            pool.sync('vps',self.directory,Path('/opt/test'),dry_run=True)
            self.assertEqual(run.call_count,1)

    def test_runtime_config_preserves_credentials_and_admin_route(self):
        config = pool.runtime_config(DATA,['198.51.100.7']).decode()
        self.assertIn('<key>test</key>',config)
        self.assertIn('dev tun0',config)
        self.assertIn('redirect-gateway def1',config)
        self.assertIn('route 198.51.100.7 255.255.255.255 net_gateway',config)

    def rotation(self, health, stopped=True):
        """Run a deterministic clock and mocked systemd while inspecting real state."""
        self.host.query.return_value = self.profiles
        clock = [0]
        def sleep(seconds):
            clock[0] += seconds
        attempts = [{'attempt_id':i+1,'vpn_id':i+1,'run_id':42} for i in range(2)]
        patches = (patch('scripts.stop_openvpn.stop_vpn',return_value=stopped),
                   patch.object(pool,'start_attempt',side_effect=attempts),
                   patch.object(pool,'finish_attempt',return_value=attempts[0]),
                   patch('scripts.ensure_openvpn.restart_vpn',return_value=True),
                   patch('scripts.ensure_openvpn.vpn_health_reason',side_effect=health))
        for p in patches:
            p.start(); self.addCleanup(p.stop)
        runner = Mock(return_value=subprocess.CompletedProcess([],0,'',''))
        result = pool.select_vpn(self.host,self.state,runner=runner,sleeper=sleep,
                                 monotonic=lambda:clock[0],config_target=self.root/'japan.conf')
        return result,clock[0],patches

    def test_timeout_then_next_vpn_one_run_and_frozen_context(self):
        checks = iter([(False,'not ready')]*30+[(True,'healthy')]*3)
        result,elapsed,_ = self.rotation(lambda *args:next(checks))
        self.assertTrue(result)
        self.assertEqual(elapsed,64)
        self.assertEqual(self.state.get('pipeline')['run_id'],'42')
        self.assertEqual(self.state.get('pipeline')['vpn']['filename'],'b.ovpn')
        self.assertEqual(os.environ['SUUMO_VPN_ID'],'2')

    def test_all_fail_and_shutdown_confirmed(self):
        result,elapsed,_ = self.rotation(lambda *args:(False,'not ready'))
        self.assertFalse(result)
        self.assertEqual(elapsed,120)
        self.assertNotIn('vpn',self.state.get('pipeline'))

    def test_unconfirmed_cleanup_blocks_every_activation(self):
        with self.assertRaises(RuntimeError): self.rotation(lambda *args:(True,'healthy'),False)
        self.assertFalse((self.root/'japan.conf').exists())

    def test_db_outage_before_selection_never_touches_vpn(self):
        self.host.query.side_effect = RuntimeError('DB down')
        with patch('scripts.stop_openvpn.stop_vpn') as stop:
            with self.assertRaises(RuntimeError): pool.select_vpn(self.host,self.state)
            stop.assert_not_called()


if __name__ == '__main__':
    unittest.main()
