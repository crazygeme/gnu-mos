"""Validate combined media builds and profile completion without compilation."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import media_build

SPEC = importlib.util.spec_from_file_location("media_lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class FFmpegBuild(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)

    def test_each_profile_has_one_compile_and_install_pass(self):
        for console in (False, True):
            env = {"LFS_WORKSPACE": str(self.workspace),
                   "LFS_SYSROOT": str(self.workspace / "sysroot"),
                   "LFS_NO_GUI": "1" if console else "0"}
            configured = {"CC": "target-gcc", "CXX": "target-g++",
                          "CFLAGS": "-O2", "LDFLAGS": ""}
            with patch.dict(os.environ, env), \
                 patch.object(media_build, "archive_source", return_value=self.workspace / "source"), \
                 patch.object(media_build, "environment", return_value=configured), \
                 patch.object(media_build.subprocess, "run") as execute:
                media_build.build_ffmpeg()
            commands = [call.args[0] for call in execute.call_args_list]
            self.assertEqual(len(commands), 3)
            self.assertIn("--enable-ffmpeg", commands[0])
            self.assertIn("--enable-ffprobe", commands[0])
            self.assertIn("--disable-ffplay" if console else "--enable-ffplay", commands[0])
            self.assertIn("--disable-vaapi" if console else "--enable-vaapi", commands[0])
            self.assertIn("--disable-libdrm" if console else "--enable-libdrm", commands[0])
            self.assertEqual(commands[1], ["make", "-j4", "all"])
            self.assertEqual(commands[2][-1], "install")

    def test_completion_covers_only_profiles_actually_built(self):
        package = self.workspace / "package"
        package.mkdir()
        (package / "version").write_text("3\n")
        info = {"name": "ffmpeg", "build-profiles": ["console", "gui"]}
        marker = self.workspace / "artifacts/ffmpeg.done"
        marker.parent.mkdir()
        for completed, console, expected in (("console", True, True),
                                              ("console", False, False),
                                              ("gui", True, True),
                                              ("gui", False, True)):
            record = {"version": 3, "build_profile": completed}
            marker.write_text(json.dumps(record))
            with patch.multiple(lfs, WORK=self.workspace, NO_GUI=console):
                self.assertEqual(lfs.artifact_current(package, info), expected)
            self.assertEqual(json.loads(marker.read_text()), record)

    def test_selection_contains_one_media_package_after_sdl(self):
        for console in (False, True):
            packages = [p.name for p in lfs.selected_packages(console)]
            self.assertEqual(packages.count("ffmpeg"), 1)
            self.assertNotIn("ffplay", packages)
            if console:
                self.assertNotIn("sdl2", packages)
                self.assertNotIn("libva", packages)
                self.assertNotIn("virglrenderer-host", packages)
            else:
                self.assertLess(packages.index("sdl2"), packages.index("ffmpeg"))
                self.assertLess(packages.index("libdrm"), packages.index("libva"))
                self.assertLess(packages.index("libva"), packages.index("mesa"))
                self.assertLess(packages.index("mesa"), packages.index("ffmpeg"))
                self.assertLess(packages.index("virglrenderer-host"), packages.index("qemu-host"))


if __name__ == "__main__":
    unittest.main()
