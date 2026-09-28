"""Validate completion versions without compiling packages."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class BuildVersions(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.directory = self.root / "packages/example"
        self.directory.mkdir(parents=True)
        self.info = {"name": "example", "version": "2.7.0", "source": "meta"}
        (self.directory / "package.json").write_text(json.dumps(self.info))
        (self.directory / "version").write_text("2\n")
        (self.directory / "build.py").touch()
        self.done = self.root / "artifacts/example.done"
        self.done.parent.mkdir()
        (self.root / "logs").mkdir()
        overrides = patch.multiple(
            lfs, WORK=self.root, SOURCES=self.root / "sources",
            PKG_ROOT=self.root / "packages", SYSROOT=self.root / "sysroot",
            IMAGE=self.root / "image",
        )
        overrides.start()
        self.addCleanup(overrides.stop)

    def test_status_and_build_use_the_same_version_comparison(self):
        for version, expected in ((None, False), (1, False), (2, True), (3, True)):
            with self.subTest(version=version):
                self.done.unlink(missing_ok=True)
                if version is not None:
                    self.done.write_text(json.dumps({"version": version}))
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    lfs.status()
                row = output.getvalue().splitlines()[-1]
                self.assertEqual(row.split()[-1] == "built", expected)
                with patch.object(lfs, "build_package") as compile_package, \
                     patch.object(lfs, "setup_workspace"), \
                     patch.object(lfs, "sync_sysroot"), \
                     contextlib.redirect_stdout(io.StringIO()):
                    lfs.build(all_mode=True, rebuild_mode=False)
                self.assertEqual(compile_package.call_count, 0 if expected else 1)

    def test_unversioned_markers_are_updated_without_compilation(self):
        for content in ('', '{"name": "example", "extra": true}'):
            for scan in ("status", "build"):
                with self.subTest(content=content, scan=scan):
                    self.done.write_text(content)
                    with patch.object(lfs, "build_package") as compile_package, \
                         patch.object(lfs, "setup_workspace"), \
                         patch.object(lfs, "sync_sysroot"), \
                         contextlib.redirect_stdout(io.StringIO()):
                        if scan == "status":
                            lfs.status()
                        else:
                            lfs.build(all_mode=True, rebuild_mode=False)
                    compile_package.assert_not_called()
                    record = json.loads(self.done.read_text())
                    self.assertEqual(record["version"], 2)
                    if content:
                        self.assertTrue(record["extra"])

    def test_successful_build_records_build_and_source_versions(self):
        with patch.object(lfs, "run"), contextlib.redirect_stdout(io.StringIO()):
            lfs.build_package(self.directory)
        self.assertEqual(json.loads(self.done.read_text()), {
            "name": "example", "version": 2, "source_version": "2.7.0",
        })

    def test_failed_build_does_not_advance_completion_version(self):
        self.done.write_text('{"version": 1}\n')
        with patch.object(lfs, "run", side_effect=RuntimeError("build failed")), \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaises(RuntimeError):
            lfs.build_package(self.directory)
        self.assertEqual(json.loads(self.done.read_text())["version"], 1)

    def test_reset_removes_only_completion_markers(self):
        preserved = ["build/object.o", "sysroot/usr/bin/example", "sources/archive.tar",
                     "tools/bin/compiler", "logs/example.log", "artifacts/nested/data", "image"]
        for relative in preserved:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative)
        self.done.touch()
        nested = self.root / "artifacts/nested/example.done"
        nested.touch()
        with patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
            lfs.reset_build_state()
            lfs.reset_build_state()
        self.assertFalse(self.done.exists())
        self.assertFalse(nested.exists())
        for relative in preserved:
            self.assertEqual((self.root / relative).read_text(), relative)

    def test_rebuild_uses_normal_selection_and_stopping_rules(self):
        second = self.directory.parent / "second"
        second.mkdir()
        second_info = dict(self.info, name="second", order=2)
        (second / "package.json").write_text(json.dumps(second_info))
        (second / "version").write_text("2\n")
        gui = self.directory.parent / "gui"
        gui.mkdir()
        (gui / "package.json").write_text(json.dumps(
            dict(self.info, name="gui", order=3, profiles=["gui"])))
        (gui / "version").write_text("2\n")
        for all_mode, no_gui, count in ((False, False, 1), (True, False, 3),
                                        (False, True, 2)):
            with self.subTest(all_mode=all_mode, no_gui=no_gui):
                for name in ("example", "second", "gui"):
                    (self.root / "artifacts" / (name + ".done")).write_text('{"version": 2}')
                with patch.object(lfs, "build_package") as compile_package, \
                     patch.object(lfs, "setup_workspace"), \
                     patch.object(lfs, "sync_sysroot") as sync, \
                     patch("builtins.input", side_effect=AssertionError("unexpected prompt")), \
                     contextlib.redirect_stdout(io.StringIO()):
                    lfs.build(all_mode=all_mode, rebuild_mode=True, no_gui=no_gui)
                self.assertEqual(compile_package.call_count, count)
                expected = lfs.selected_packages(no_gui)[:count]
                self.assertEqual([call.args[0] for call in compile_package.call_args_list], expected)
                self.assertFalse(list((self.root / "artifacts").rglob("*.done")))
                sync.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
