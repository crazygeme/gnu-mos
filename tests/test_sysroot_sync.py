"""Validate sysroot overlay replacement without compiling packages."""

import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class SysrootSync(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "src/sysroot/etc"
        self.destination = self.root / "sysroot/etc"
        self.source.mkdir(parents=True)
        self.destination.mkdir(parents=True)
        overrides = patch.multiple(lfs, ROOT=self.root, SYSROOT=self.destination.parent)
        overrides.start()
        self.addCleanup(overrides.stop)

    def test_read_only_overlay_and_symlinks(self):
        source = self.source / "sudoers"
        source.write_text("%sudo ALL=(ALL:ALL) ALL\n")
        source.chmod(0o640)
        destination = self.destination / "sudoers"
        destination.write_text("package defaults\n")
        destination.chmod(0o440)
        (self.source / "mtab").symlink_to("/proc/mounts")
        (self.destination / "mtab").symlink_to("/proc/self/mounts")
        (self.destination / "package.conf").write_text("retained\n")

        lfs.sync_sysroot()
        destination.chmod(0o440)
        lfs.sync_sysroot()

        self.assertEqual(destination.read_text(), source.read_text())
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o640)
        self.assertEqual((self.destination / "mtab").readlink(), Path("/proc/mounts"))
        self.assertEqual((self.destination / "package.conf").read_text(), "retained\n")


if __name__ == "__main__":
    unittest.main()
