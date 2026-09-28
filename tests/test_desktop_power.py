"""Validate desktop power integration without executing system power commands."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SYSROOT = ROOT / "src/sysroot"


class ShutdownRunlevels(unittest.TestCase):
    def run_level(self, level, terminal_status=0):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            commands = fixture / "bin"
            commands.mkdir()
            log = fixture / "commands.log"
            log.touch()
            for name in ("killall5", "sleep", "sync", "umount", "mount", "poweroff", "reboot"):
                program = commands / name
                program.write_text(
                    '#!/bin/sh\nprintf "%s" "${0##*/}" >> "$POWER_TEST_LOG"\n'
                    'for arg do printf " %s" "$arg" >> "$POWER_TEST_LOG"; done\n'
                    'printf "\\n" >> "$POWER_TEST_LOG"\n'
                    'case "${0##*/}" in poweroff|reboot) exit "$POWER_TEST_STATUS";; esac\n'
                )
                program.chmod(0o755)

            services = fixture / "rc3.d"
            services.mkdir()
            forbidden_start = services / "S10service"
            forbidden_start.write_text('#!/bin/sh\nprintf "unexpected-start\\n" >> "$POWER_TEST_LOG"\n')
            forbidden_start.chmod(0o755)
            functions = fixture / "boot-functions"
            functions.write_text('boot_action() { shift; "$@"; }\n')
            source = (SYSROOT / "etc/init.d/rc").read_text()
            source = source.replace('PATH=/sbin:/bin:/usr/sbin:/usr/bin', f'PATH={commands}')
            source = source.replace('/etc/init.d/boot-functions', str(functions))
            source = source.replace('/etc/rc3.d', str(services))
            source = source.replace('/sbin/', str(commands) + '/')
            script = fixture / "rc"
            script.write_text(source)
            env = dict(os.environ, POWER_TEST_LOG=str(log), POWER_TEST_STATUS=str(terminal_status))
            result = subprocess.run(['/bin/sh', str(script), str(level)], env=env,
                                    capture_output=True, text=True, timeout=5)
            return result.returncode, log.read_text().splitlines()

    def test_shutdown_and_restart_order(self):
        common = ["killall5 -15", "sleep 2", "killall5 -9", "sync",
                  "umount -a -r", "mount -n -o remount,ro /", "sync"]
        for level, terminal in ((0, "poweroff"), (6, "reboot")):
            with self.subTest(level=level):
                status, commands = self.run_level(level)
                self.assertEqual(status, 0)
                self.assertEqual(commands, common + [terminal + " -f"])

    def test_terminal_failure_does_not_start_services(self):
        status, commands = self.run_level(6, terminal_status=23)
        self.assertEqual(status, 23)
        self.assertNotIn("unexpected-start", commands)

    def test_invalid_runlevel_does_not_run_commands(self):
        status, commands = self.run_level(9)
        self.assertEqual(status, 1)
        self.assertEqual(commands, [])

    def test_init_runs_power_actions_once(self):
        entries = [line.split(":", 3) for line in (SYSROOT / "etc/inittab").read_text().splitlines()]
        for level in ("0", "6"):
            matches = [entry for entry in entries if entry[1] == level]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0][2:], ["wait", "/etc/init.d/rc " + level])


class PowerPolicy(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is required to evaluate JavaScript policy rules")
    def test_only_the_power_helper_is_authorized_for_sudo_members(self):
        rule = SYSROOT / "etc/polkit-1/rules.d/49-mos-power.rules"
        driver = '''
const fs = require("fs");
const vm = require("vm");
let rule;
vm.runInNewContext(fs.readFileSync(process.argv[1], "utf8"), {
    polkit: {Result: {YES: "yes"}, addRule: fn => { rule = fn; }}
});
const action = "org.xfce.session.xfsm-shutdown-helper";
const check = (id, groups) => rule({id}, {isInGroup: group => groups.includes(group)}) ?? null;
console.log(JSON.stringify([
    check(action, ["sudo"]), check(action, []),
    check(action, ["users"]), check("org.freedesktop.policykit.exec", ["sudo"])
]));
'''
        result = subprocess.run([shutil.which("node"), "-e", driver, str(rule)],
                                capture_output=True, text=True, check=True, timeout=5)
        self.assertEqual(json.loads(result.stdout), ["yes", None, None, None])


if __name__ == "__main__":
    unittest.main()
