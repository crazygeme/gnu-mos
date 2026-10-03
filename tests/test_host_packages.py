"""Validate host dependency installation without changing host packages."""

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class HostPackages(unittest.TestCase):
    def setUp(self):
        self.info = {
            "name": "qemu-host",
            "host-packages": {"apt": ["libsdl2-dev", "libdrm-dev"]},
        }
        lookup = patch.object(lfs.shutil, "which", side_effect=lambda name, **kw: "/usr/bin/" + name)
        lookup.start()
        self.addCleanup(lookup.stop)

    def test_packages_without_declaration_skip_package_manager(self):
        with patch.object(lfs.subprocess, "run") as query, \
             patch.object(lfs, "sudo_run") as install:
            lfs.ensure_host_packages({"name": "example"})
        query.assert_not_called()
        install.assert_not_called()

    def test_installed_dependencies_skip_installation(self):
        result = subprocess.CompletedProcess([], 0, "install ok installed")
        with patch.object(lfs.subprocess, "run", return_value=result), \
             patch.object(lfs, "sudo_run") as install:
            lfs.ensure_host_packages(self.info)
        install.assert_not_called()

    def test_absent_and_partially_installed_dependencies_are_installed(self):
        for result in (
            subprocess.CompletedProcess([], 1, ""),
            subprocess.CompletedProcess([], 0, "install ok unpacked"),
        ):
            with self.subTest(result=result), \
                 patch.object(lfs.subprocess, "run", side_effect=[
                     subprocess.CompletedProcess([], 0, "install ok installed"), result,
                 ]), patch.object(lfs, "sudo_run") as install:
                lfs.ensure_host_packages(self.info)
            install.assert_called_once_with(
                "/usr/bin/apt-get", "install", "--yes", "libdrm-dev"
            )

    def test_unsupported_host_reports_required_packages(self):
        with patch.object(lfs.shutil, "which", return_value=None), \
             patch.object(lfs, "sudo_run") as install, \
             self.assertRaisesRegex(SystemExit, "libsdl2-dev libdrm-dev"):
            lfs.ensure_host_packages(self.info)
        install.assert_not_called()

    def test_failed_installation_stops_before_source_preparation(self):
        failure = subprocess.CalledProcessError(100, ["apt-get", "install"])
        with patch.object(lfs, "metadata", return_value=self.info), \
             patch.object(lfs.subprocess, "run", return_value=
                          subprocess.CompletedProcess([], 1, "")), \
             patch.object(lfs, "sudo_run", side_effect=failure), \
             patch.object(lfs.shutil, "rmtree") as cleanup, \
             patch.object(lfs, "ensure_archive") as fetch, \
             self.assertRaises(subprocess.CalledProcessError):
            lfs.build_package(Path("unused"))
        cleanup.assert_not_called()
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
