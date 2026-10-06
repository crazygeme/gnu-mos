"""Validate Debian binary package import without compilation or network access."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lfs = load("deb_lfs", "src/lfs.py")
deb = load("deb_package", "src/deb_package.py")


class DebPackages(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.directory = self.base / "packages/example"
        self.directory.mkdir(parents=True)
        self.info = {
            "name": "example", "deb-package": "example-binary",
            "version": "1.2.3-4", "source": "deb",
            "architectures": ["x64"], "profiles": ["gui"],
            "url": "https://example.invalid/example_{version}_amd64.deb",
            "archive": "example_1.2.3-4_amd64.deb",
        }
        (self.directory / "package.json").write_text(json.dumps(self.info))
        (self.directory / "version").write_text("1\n")
        overrides = patch.multiple(
            lfs, BASE_WORK=self.base / "workspace", WORK=self.base / "workspace/x64",
            SOURCES=self.base / "workspace/sources",
            SYSROOT=self.base / "workspace/x64/sysroot", PKG_ROOT=self.base / "packages",
            IMAGE=self.base / "workspace/x64/image", ARCH="x64", NO_GUI=False,
        )
        overrides.start()
        self.addCleanup(overrides.stop)

    def environment(self):
        return {
            "LFS_PACKAGE_DIR": str(self.directory), "LFS_SOURCES": str(lfs.SOURCES),
            "LFS_SYSROOT": str(lfs.SYSROOT), "LFS_ARCH": lfs.ARCH,
            "LFS_WORKSPACE": str(lfs.WORK),
        }

    def make_deb(self, *, architecture="amd64", name="example-binary", version="1.2.3-4"):
        if not shutil.which("dpkg-deb") or not shutil.which("tar"):
            self.skipTest("host dpkg-deb and GNU tar are required")
        payload = self.base / "payload"
        (payload / "DEBIAN").mkdir(parents=True)
        (payload / "DEBIAN/control").write_text(
            f"Package: {name}\nVersion: {version}\nArchitecture: {architecture}\n"
            "Maintainer: Package Tests <tests@example.invalid>\n"
            "Description: Binary extraction fixture\n"
        )
        self.hook_marker = self.base / "maintainer-script-ran"
        hook = payload / "DEBIAN/postinst"
        hook.write_text(f"#!/bin/sh\ntouch '{self.hook_marker}'\n")
        hook.chmod(0o755)
        (payload / "bin").mkdir()
        executable = payload / "bin/example"
        executable.write_bytes(b"binary payload\n")
        executable.chmod(0o755)
        (payload / "bin/example-link").symlink_to("/usr/bin/example")
        os.link(executable, payload / "bin/example-hardlink")
        (payload / "usr/share/applications").mkdir(parents=True)
        (payload / "usr/share/applications/example.desktop").write_text(
            "[Desktop Entry]\nType=Application\nName=Example\nExec=example\n"
        )
        lfs.SOURCES.mkdir(parents=True, exist_ok=True)
        archive = lfs.SOURCES / self.info["archive"]
        subprocess.run(
            ["dpkg-deb", "--build", "--root-owner-group", str(payload), str(archive)],
            stdout=subprocess.DEVNULL, check=True,
        )
        self.info["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        (self.directory / "package.json").write_text(json.dumps(self.info))
        return archive

    def test_binary_import_preserves_payload_and_records_completion(self):
        self.make_deb()
        lfs.setup_workspace()
        self.assertEqual(lfs.package_state(self.directory, self.info), "fetched")
        with patch.object(lfs.urllib.request, "urlretrieve") as download, \
             contextlib.redirect_stdout(io.StringIO()):
            lfs.build_package(self.directory)
            lfs.build_package(self.directory)
        download.assert_not_called()
        executable = lfs.SYSROOT / "usr/bin/example"
        self.assertEqual(executable.read_bytes(), b"binary payload\n")
        self.assertEqual(executable.stat().st_mode & 0o777, 0o755)
        self.assertEqual((lfs.SYSROOT / "bin").readlink(), Path("usr/bin"))
        self.assertEqual((lfs.SYSROOT / "usr/bin/example-link").readlink(), Path("/usr/bin/example"))
        self.assertEqual(executable.stat().st_ino, (lfs.SYSROOT / "usr/bin/example-hardlink").stat().st_ino)
        self.assertTrue((lfs.SYSROOT / "usr/share/applications/example.desktop").is_file())
        self.assertFalse(self.hook_marker.exists())
        self.assertFalse((lfs.SYSROOT / "DEBIAN").exists())
        self.assertFalse((lfs.SYSROOT / "var/lib/dpkg/status").exists())
        self.assertEqual(json.loads(lfs.artifact(self.directory, self.info).read_text()), {
            "name": "example", "version": 1, "source_version": "1.2.3-4",
        })
        self.assertEqual(lfs.package_state(self.directory, self.info), "built")

    def test_all_architecture_payload_is_accepted(self):
        self.make_deb(architecture="all")
        with patch.dict(os.environ, self.environment()):
            deb.install_deb()
        self.assertTrue((lfs.SYSROOT / "bin/example").exists())

    def test_control_mismatch_prevents_extraction_and_completion(self):
        for field, value in (("architecture", "i386"), ("name", "other"), ("version", "9.0-1")):
            with self.subTest(field=field):
                shutil.rmtree(self.base / "payload", ignore_errors=True)
                self.make_deb(**{field: value})
                lfs.setup_workspace()
                done = lfs.artifact(self.directory, self.info)
                done.parent.mkdir(parents=True, exist_ok=True)
                done.write_text('{"version": 1, "source_version": "0.9-1"}\n')
                before = done.read_bytes()
                with contextlib.redirect_stdout(io.StringIO()), \
                     self.assertRaises(subprocess.CalledProcessError):
                    lfs.build_package(self.directory)
                self.assertEqual(done.read_bytes(), before)
                self.assertFalse((lfs.SYSROOT / "usr/bin/example").exists())

    def test_architecture_and_console_selection_exclude_examples(self):
        self.assertEqual(lfs.selected_packages(False), [self.directory])
        self.assertEqual(lfs.selected_packages(True), [])
        lfs.select_workspace(False, "x86")
        self.assertEqual(lfs.selected_packages(False), [])
        with patch.object(lfs, "fetch_package") as fetch, \
             self.assertRaisesRegex(SystemExit, "does not support x86"):
            lfs.build_package(self.directory)
        fetch.assert_not_called()

    def test_download_is_cached_and_checked_before_promotion(self):
        content = b"Debian download fixture"
        self.info["sha256"] = hashlib.sha256(content).hexdigest()

        def download(url, destination, reporthook):
            self.assertEqual(url, "https://example.invalid/example_1.2.3-4_amd64.deb")
            destination.write_bytes(content)

        with patch.object(lfs.urllib.request, "urlretrieve", side_effect=download) as retrieve, \
             contextlib.redirect_stdout(io.StringIO()):
            lfs.fetch_package(self.info)
            lfs.fetch_package(self.info)
        self.assertEqual(retrieve.call_count, 1)
        archive = lfs.SOURCES / self.info["archive"]
        archive.write_bytes(b"corrupt cache")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            lfs.fetch_package(self.info)
        archive.unlink()
        self.info["sha256"] = "0" * 64
        with patch.object(lfs.urllib.request, "urlretrieve", side_effect=download), \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            lfs.fetch_package(self.info)
        self.assertFalse(archive.exists())
        self.assertFalse(archive.with_suffix(".deb.part").exists())

    def test_download_failure_removes_partial_archive(self):
        def download(url, destination, reporthook):
            destination.write_bytes(b"partial")
            raise OSError("connection interrupted")

        with patch.object(lfs.urllib.request, "urlretrieve", side_effect=download), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(OSError):
            lfs.fetch_package(self.info)
        self.assertFalse((lfs.SOURCES / self.info["archive"]).exists())
        self.assertFalse((lfs.SOURCES / (self.info["archive"] + ".part")).exists())


if __name__ == "__main__":
    unittest.main()
