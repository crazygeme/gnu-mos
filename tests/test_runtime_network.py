"""Validate scoped NAT setup and cleanup for the QEMU network."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('runtime_network_lfs', ROOT / 'src/lfs.py')
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class RuntimeNetwork(unittest.TestCase):
    def test_nat_applies_to_all_egress_routes_and_is_removed(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(lfs, 'WORK', Path(directory)), \
             patch.object(lfs, 'sudo_run') as start, \
             patch.object(lfs, 'cleanup_network') as cleanup, \
             patch.object(lfs.subprocess, 'check_output', return_value='1\n'):
            with lfs.qemu_network():
                (Path(directory) / 'lfs-dnsmasq.pid').write_text('31415')
            rules = [call.args for call in start.call_args_list if call.args[0] == 'iptables']
            nat = [rule for rule in rules if '-t' in rule and 'nat' in rule]
            self.assertEqual(nat, [('iptables', '-t', 'nat', '-A', 'POSTROUTING',
                                   '-s', '10.0.6.0/24', '-j', 'MASQUERADE')])
            cleanup.assert_any_call('iptables', '-t', 'nat', '-D', 'POSTROUTING',
                                    '-s', '10.0.6.0/24', '-j', 'MASQUERADE')
            cleanup.assert_any_call('kill', '31415')
            self.assertFalse((Path(directory) / 'lfs-dnsmasq.pid').exists())

    def test_failed_service_start_restores_forwarding_and_scoped_rules(self):
        def start(*command):
            if command[0] == 'dnsmasq':
                raise RuntimeError('DNS service unavailable')
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(lfs, 'WORK', Path(directory)), \
             patch.object(lfs, 'sudo_run', side_effect=start), \
             patch.object(lfs, 'cleanup_network') as cleanup, \
             patch.object(lfs.subprocess, 'check_output', return_value='0\n'):
            with self.assertRaises(RuntimeError):
                with lfs.qemu_network():
                    self.fail('Network initialization must fail')
            cleanup.assert_any_call('sysctl', '-qw', 'net.ipv4.ip_forward=0')
            cleanup.assert_any_call('iptables', '-t', 'nat', '-D', 'POSTROUTING',
                                    '-s', '10.0.6.0/24', '-j', 'MASQUERADE')
            cleanup.assert_any_call('ip', 'tuntap', 'del', 'dev', 'lfs-tap0', 'mode', 'tap')
            self.assertFalse(any(call.args[0] == 'kill' for call in cleanup.call_args_list))


if __name__ == '__main__':
    unittest.main()
