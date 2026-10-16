"""Validate Clang package selection and integration without compilation."""

import importlib.util
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "src/packages"
spec = importlib.util.spec_from_file_location("clang_lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lfs)


class ClangPackages(unittest.TestCase):
    def test_binary_dependency_closure_is_selected_in_build_order(self):
        for console in (False, True):
            with self.subTest(console=console), patch.object(lfs, "ARCH", "x64"):
                selected = lfs.selected_packages(console)
                positions = {p.name: i for i, p in enumerate(selected)}
                pending = ["clang-tools"]
                seen = set()
                while pending:
                    name = pending.pop()
                    if name in seen:
                        continue
                    seen.add(name)
                    info = lfs.metadata(PACKAGES / name)
                    for dependency in info.get("dependencies", []):
                        self.assertIn(dependency, positions)
                        self.assertLess(positions[dependency], positions[name])
                        pending.append(dependency)
                    if info["source"] == "deb":
                        self.assertEqual(info["architectures"], ["x64"])
                        self.assertEqual(len(info["sha256"]), 64)
                        self.assertTrue(info["archive"].endswith("_amd64.deb"))
                        self.assertGreater(int((PACKAGES / name / "version").read_text()), 0)
                self.assertTrue({"clang", "clang-format", "clangd", "libgrpc29t64",
                                 "libllvm19", "libclang-common-19-dev", "libc++-dev",
                                 "libc++abi-dev", "libc++1-19", "libc++abi1-19",
                                 "libunwind-19", "libunwind-19-dev"} <= seen)
        with patch.object(lfs, "ARCH", "x86"):
            self.assertFalse({"clang", "clang-tools", "clang-format", "clangd",
                              "libc++-dev", "libc++abi-dev", "libc++1-19",
                              "libc++abi1-19", "libunwind-19", "libunwind-19-dev"} &
                             {p.name for p in lfs.selected_packages(False)})

    def test_postscripts_supply_commands_and_preserve_system_libraries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            library = root / "usr/lib"
            multiarch = library / "x86_64-linux-gnu"
            tools = library / "llvm-19/bin"
            commands = root / "usr/bin"
            for directory in (multiarch, tools, commands):
                directory.mkdir(parents=True)
            (multiarch / "libLLVM.so.19.1").write_bytes(b"library")
            (multiarch / "libLLVM-19.so").symlink_to("libLLVM.so.19.1")
            (multiarch / "libstdc++.so.6").write_bytes(b"unused library")
            (library / "libstdc++.so.6").write_bytes(b"system library")
            llvm_libraries = library / "llvm-19/lib"
            llvm_libraries.mkdir()
            for name in ("libc++", "libc++abi", "libunwind"):
                (llvm_libraries / (name + ".so.1")).write_bytes(b"runtime library")
                (multiarch / (name + ".so.1")).symlink_to("../llvm-19/lib/" + name + ".so.1")
                (multiarch / (name + ".so")).symlink_to(name + ".so.1")
            for name in ("clang", "clang++", "clang-cpp", "clang-format", "clangd",
                         "clang-check", "scan-build"):
                (tools / name).write_text("#!/bin/sh\n")
                (tools / name).chmod(0o755)
            (tools / "README").write_text("tool data")
            for name in ("clang", "clang++", "clang-cpp"):
                (commands / (name + "-19")).symlink_to("../lib/llvm-19/bin/" + name)
            env = {"LFS_SYSROOT": str(root), "LFS_TARGET": "x86_64-lfs-linux-gnu"}
            with patch.dict(os.environ, env):
                for _ in range(2):
                    for package in ("clang", "clang-tools"):
                        runpy.run_path(str(PACKAGES / package / "postscript.py"))
            self.assertEqual((library / "libLLVM-19.so").read_bytes(), b"library")
            self.assertEqual((library / "libstdc++.so.6").read_bytes(), b"system library")
            for name in ("libc++", "libc++abi", "libunwind"):
                self.assertEqual((library / (name + ".so")).read_bytes(), b"runtime library")
            for name in ("clang", "clang++", "clang-format", "clangd", "clang-check", "scan-build"):
                self.assertEqual((commands / name).resolve(), tools / name)
            self.assertFalse((commands / "README").exists())
            gcc = json.loads((PACKAGES / "gcc-target/package.json").read_text())
            for name in ("clang", "clang++", "clang-cpp"):
                config = (tools / (name + ".cfg")).read_text()
                self.assertIn("--target=x86_64-lfs-linux-gnu\n", config)
                self.assertIn("/usr/lib/gcc/x86_64-lfs-linux-gnu/" + gcc["version"], config)


if __name__ == "__main__":
    unittest.main()
