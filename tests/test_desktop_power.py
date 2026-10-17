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
