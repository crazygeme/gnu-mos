"""Validate build preparation without network access or compilation."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("preparation_lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class BuildPreparation(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        override = patch.object(lfs, "SOURCES", Path(temporary.name))
        override.start()
        self.addCleanup(override.stop)
        self.directories = [Path(f"package-{index}") for index in range(8)]
        self.infos = {
            directory: {
                "name": directory.name, "version": "1", "source": "deb",
                "archive": directory.name + ".deb",
                "url": "https://example.invalid/" + directory.name,
                "host-packages": {"apt": ["shared-dev", directory.name + "-dev"]},
            }
            for directory in self.directories
        }

    def test_dependencies_are_deduplicated_and_installed_before_downloads(self):
        events = []
        def query(*args, **kwargs):
            return subprocess.CompletedProcess([], 1, "")
        def install(*args):
            events.append("install")
        def fetch(info):
            self.assertEqual(events[0], "install")
            events.append("download")
        with patch.object(lfs, "metadata", side_effect=self.infos.__getitem__), \
             patch.object(lfs.shutil, "which", side_effect=lambda name, **kw: name), \
             patch.object(lfs.subprocess, "run", side_effect=query), \
             patch.object(lfs, "sudo_run", side_effect=install) as apt, \
             patch.object(lfs, "prepare_source", side_effect=fetch), \
             contextlib.redirect_stdout(io.StringIO()):
            lfs.prepare_packages(self.directories)
        apt.assert_called_once_with(
            "apt-get", "install", "--yes", "shared-dev",
            *(directory.name + "-dev" for directory in self.directories),
        )
        self.assertEqual(events, ["install"] + ["download"] * 8)

    def test_downloads_run_concurrently_with_limit_four(self):
        barrier = threading.Barrier(4, timeout=5)
        lock = threading.Lock()
        active = 0
        maximum = 0
        def retrieve(url, destination, reporthook):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            barrier.wait()
            destination.write_bytes(b"download fixture")
            with lock:
                active -= 1
        with patch.object(lfs, "metadata", side_effect=self.infos.__getitem__), \
             patch.object(lfs, "ensure_host_packages"), \
             patch.object(lfs.urllib.request, "urlretrieve", side_effect=retrieve), \
             contextlib.redirect_stdout(io.StringIO()):
            lfs.prepare_packages(self.directories)
        self.assertEqual(maximum, 4)
        for info in self.infos.values():
            self.assertEqual((lfs.SOURCES / info["archive"]).read_bytes(), b"download fixture")

    def test_shared_source_is_downloaded_once(self):
        for info in self.infos.values():
            info["archive"] = "shared.deb"
        def retrieve(url, destination, reporthook):
            destination.write_bytes(b"shared fixture")
        with patch.object(lfs, "metadata", side_effect=self.infos.__getitem__), \
             patch.object(lfs, "ensure_host_packages"), \
             patch.object(lfs.urllib.request, "urlretrieve", side_effect=retrieve) as download, \
             contextlib.redirect_stdout(io.StringIO()):
            lfs.prepare_packages(self.directories)
        download.assert_called_once()

    def test_corrupt_archive_is_replaced_during_preparation(self):
        info = dict(self.infos[self.directories[0]], source="archive", archive="source.tar")
        archive = lfs.SOURCES / info["archive"]
        archive.write_bytes(b"invalid archive")
        def retrieve(url, destination, reporthook):
            with tarfile.open(destination, "w") as source:
                source.addfile(tarfile.TarInfo("source/"))
        with patch.object(lfs.urllib.request, "urlretrieve", side_effect=retrieve) as download, \
             contextlib.redirect_stdout(io.StringIO()):
            lfs.prepare_source(info)
        download.assert_called_once()
        with tarfile.open(archive) as source:
            self.assertEqual(source.getnames(), ["source/"])

    def test_invalid_replacement_archive_stops_preparation(self):
        info = dict(self.infos[self.directories[0]], source="archive", archive="source.tar")
        def retrieve(url, destination, reporthook):
            destination.write_bytes(b"invalid archive")
        with patch.object(lfs.urllib.request, "urlretrieve", side_effect=retrieve), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(tarfile.TarError):
            lfs.prepare_source(info)

    def test_no_pending_packages_skip_preparation(self):
        with patch.object(lfs, "ensure_host_packages") as install, \
             patch.object(lfs, "prepare_source") as download:
            lfs.prepare_packages([])
        install.assert_not_called()
        download.assert_not_called()

    def test_installation_failure_prevents_downloads(self):
        with patch.object(lfs, "metadata", side_effect=self.infos.__getitem__), \
             patch.object(lfs, "ensure_host_packages", side_effect=RuntimeError("apt failed")), \
             patch.object(lfs, "prepare_source") as download, \
             self.assertRaisesRegex(RuntimeError, "apt failed"):
            lfs.prepare_packages(self.directories)
        download.assert_not_called()

    def test_build_prepares_selected_packages_before_compilation(self):
        for all_mode, no_gui, count in ((False, False, 1), (True, False, 8), (False, True, 8)):
            with self.subTest(all_mode=all_mode, no_gui=no_gui):
                events = []
                with patch.object(lfs, "setup_workspace"), \
                     patch.object(lfs, "selected_packages", return_value=self.directories), \
                     patch.object(lfs, "metadata", side_effect=self.infos.__getitem__), \
                     patch.object(lfs, "package_state", return_value="empty"), \
                     patch.object(lfs, "prepare_packages", side_effect=lambda ds: events.append(ds)), \
                     patch.object(lfs, "build_package", side_effect=lambda d, **kw: events.append(d)), \
                     patch.object(lfs, "sync_sysroot"), \
                     contextlib.redirect_stdout(io.StringIO()):
                    lfs.build(all_mode=all_mode, no_gui=no_gui)
                self.assertEqual(events, [self.directories[:count]] + self.directories[:count])

    def test_download_failure_prevents_compilation(self):
        with patch.object(lfs, "setup_workspace"), \
             patch.object(lfs, "selected_packages", return_value=self.directories), \
             patch.object(lfs, "metadata", side_effect=self.infos.__getitem__), \
             patch.object(lfs, "package_state", return_value="empty"), \
             patch.object(lfs, "ensure_host_packages"), \
             patch.object(lfs, "prepare_source", side_effect=OSError("download failed")), \
             patch.object(lfs, "build_package") as compile_package, \
             self.assertRaisesRegex(OSError, "download failed"):
            lfs.build(all_mode=True)
        compile_package.assert_not_called()


if __name__ == "__main__":
    unittest.main()
