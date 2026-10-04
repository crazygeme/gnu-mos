"""Validate architecture isolation without compilation."""

import contextlib
import importlib.util
import io
import json
import os
import runpy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lfs = load("architecture_lfs", "src/lfs.py")
package_lib = load("architecture_package_lib", "src/package_lib.py")


class Architectures(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name) / "workspace"
        self.base.mkdir()
        overrides = patch.multiple(lfs, BASE_WORK=self.base)
        overrides.start()
        self.addCleanup(overrides.stop)

    def test_architecture_selection_leaves_installed_files_unchanged(self):
        paths = ("sysroot/file", "tools/bin/compiler", "x86/artifacts/example.done",
                 "x64/artifacts/example.done", "sources/archive.tar")
        for relative in paths:
            path = self.base / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative)
        for arch in ("x86", "x64"):
            lfs.select_workspace(False, arch)
            self.assertEqual(lfs.WORK, self.base / arch)
        for relative in paths:
            self.assertEqual((self.base / relative).read_text(), relative)
        self.assertFalse(any(path.is_symlink() for path in self.base.iterdir()))

    def test_source_archive_is_downloaded_once_for_both_architectures(self):
        info = {"name": "example", "source": "archive", "version": "1",
                "archive": "example.tar", "url": "https://example.invalid/example.tar"}
        def retrieve(url, path, reporthook):
            path.write_bytes(b"shared source")
        with patch.object(lfs.urllib.request, "urlretrieve", side_effect=retrieve) as download:
            for arch in ("x86", "x64"):
                lfs.select_workspace(False, arch)
                lfs.setup_workspace()
                lfs.fetch_package(info)
        self.assertEqual(download.call_count, 1)
        self.assertEqual(lfs.SOURCES, self.base / "sources")

    def test_target_environment_and_library_paths(self):
        for arch, bits, target in (("x86", "32", "i686-lfs-linux-gnu"),
                                   ("x64", "64", "x86_64-lfs-linux-gnu")):
            with self.subTest(arch=arch):
                lfs.select_workspace(False, arch)
                lfs.setup_workspace()
                env = {**lfs.architecture_environment(),
                       "LFS_WORKSPACE": str(lfs.WORK), "LFS_SYSROOT": str(lfs.SYSROOT)}
                with patch.dict(os.environ, env):
                    configured = package_lib.environment()
                self.assertEqual(configured["CC"], target + "-gcc")
                self.assertEqual(configured["CFLAGS"], "-O2 -m" + bits)
                self.assertEqual(lfs.IMAGE, self.base / arch / "qemu-hd/lfs.img")
                if arch == "x64":
                    self.assertEqual((lfs.SYSROOT / "lib64").resolve(), lfs.SYSROOT / "usr/lib")
                    self.assertEqual((lfs.SYSROOT / "usr/lib64").resolve(), lfs.SYSROOT / "usr/lib")

    def test_rebuild_keeps_other_architecture_markers(self):
        for arch in ("x86", "x64"):
            marker = self.base / arch / "artifacts/example.done"
            marker.parent.mkdir(parents=True)
            marker.write_text('{"version": 7}')
        lfs.select_workspace(False, "x64")
        lfs.reset_build_state()
        self.assertTrue((self.base / "x86/artifacts/example.done").is_file())
        self.assertFalse((self.base / "x64/artifacts/example.done").exists())

    def test_setup_routes_to_selected_image_without_accessing_it(self):
        for arch in ("x86", "x64"):
            with patch.object(lfs, "sync_sysroot"), patch.object(lfs, "run_postscripts"), \
                 patch.object(lfs, "create_image") as install:
                lfs.main(["setup", "--arch", arch])
                install.assert_called_once_with()
                self.assertEqual(lfs.IMAGE, self.base / arch / "qemu-hd/lfs.img")

    def test_cli_accepts_architecture_before_and_after_subcommand(self):
        for argv in (["status"], ["stats"], ["--arch", "x64", "status"], ["status", "--arch", "x64"],
                     ["stats", "--arch", "x64"]):
            with patch.object(lfs, "status") as status:
                self.assertEqual(lfs.main(argv), 0)
                status.assert_called_once_with(False)
                self.assertEqual(lfs.ARCH, "x64")

    def test_meson_machine_matches_selected_architecture(self):
        for arch, family, cpu in (("x86", "x86", "i686"),
                                  ("x64", "x86_64", "x86_64")):
            lfs.select_workspace(False, arch)
            lfs.setup_workspace()
            env = {**lfs.architecture_environment(),
                   "LFS_WORKSPACE": str(lfs.WORK), "LFS_SYSROOT": str(lfs.SYSROOT)}
            with patch.dict(os.environ, env), \
                 patch.object(package_lib, "host_tool_paths", return_value={"pkg-config": "/usr/bin/pkg-config"}), \
                 patch.object(package_lib.subprocess, "run"):
                package_lib.meson_install(self.base / "source", "example", host_tools=())
            cross = (lfs.WORK / "build/example-meson/cross-file.ini").read_text()
            self.assertIn(f"cpu_family = '{family}'", cross)
            self.assertIn(f"cpu = '{cpu}'", cross)
            self.assertIn(f"c = '{lfs.TARGETS[arch]}-gcc'", cross)

    def test_mos_installs_bootable_artifact_for_selected_architecture(self):
        checkout = self.base / "sources/mos"
        checkout.mkdir(parents=True)
        (checkout / "Makefile").touch()
        for arch, filename in (("x86", "kernel"), ("x64", "kernel.boot")):
            lfs.select_workspace(False, arch)
            lfs.setup_workspace()
            env = {**lfs.architecture_environment(), "LFS_WORKSPACE": str(lfs.WORK),
                   "LFS_SYSROOT": str(lfs.SYSROOT), "LFS_SOURCES": str(lfs.SOURCES)}
            with patch.dict(os.environ, env), patch("subprocess.check_output", return_value=b""), \
                 patch("subprocess.run") as compile_kernel, patch("shutil.copy2") as install:
                runpy.run_path(str(ROOT / "src/packages/mos/build.py"))
            self.assertIn("ARCH=" + arch, compile_kernel.call_args.args[0])
            install.assert_called_once_with(lfs.WORK / "build/mos/out" / arch / "release" / filename,
                                            lfs.SYSROOT / "boot/kernel")

    def test_build_and_postscript_receive_architecture_environment(self):
        directory = self.base.parent / "packages/example"
        directory.mkdir(parents=True)
        (directory / "package.json").write_text(json.dumps(
            {"name": "example", "source": "meta", "version": "1"}))
        (directory / "version").write_text("1\n")
        (directory / "build.py").touch()
        (directory / "postscript.py").touch()
        for arch in ("x86", "x64"):
            lfs.select_workspace(False, arch)
            lfs.setup_workspace()
            with patch.object(lfs, "run") as execute, \
                 patch.object(lfs, "package_dirs", return_value=[directory]), \
                 contextlib.redirect_stdout(io.StringIO()):
                lfs.build_package(directory)
                lfs.run_postscripts()
            self.assertEqual(execute.call_count, 2)
            for call in execute.call_args_list:
                env = call.kwargs["env"]
                self.assertEqual(env["LFS_ARCH"], arch)
                self.assertEqual(env["LFS_WORKSPACE"], str(self.base / arch))
                self.assertEqual(env["LFS_SOURCES"], str(self.base / "sources"))


if __name__ == "__main__":
    unittest.main()
