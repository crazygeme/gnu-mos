"""Validate binary application dependency configuration without compilation."""

import importlib.util
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("runtime_lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lfs)
sys.path.insert(0, str(ROOT / "src"))
import package_lib


class BinaryRuntime(unittest.TestCase):
    def test_runtime_packages_precede_binary_applications(self):
        for arch in ("x86", "x64"):
            with self.subTest(arch=arch), patch.object(lfs, "ARCH", arch):
                packages = lfs.selected_packages(False)
                positions = {path.name: index for index, path in enumerate(packages)}
                for name in ("nspr", "nss", "cups"):
                    self.assertIn(name, positions)
                    info = lfs.metadata(ROOT / "src/packages" / name)
                    for dependency in info["dependencies"]:
                        self.assertLess(positions[dependency], positions[name])
                    self.assertNotIn(name, [p.name for p in lfs.selected_packages(True)])
                if arch == "x64":
                    for name in ("vscode", "microsoft-edge"):
                        info = lfs.metadata(ROOT / "src/packages" / name)
                        self.assertEqual(set(info["dependencies"]), {"nspr", "nss", "cups"})
                        for dependency in info["dependencies"]:
                            self.assertLess(positions[dependency], positions[name])

    def test_nspr_configures_native_tools_and_selected_target_abi(self):
        for arch, bits, target in (("x86", "32", "i686-lfs-linux-gnu"),
                                   ("x64", "64", "x86_64-lfs-linux-gnu")):
            with self.subTest(arch=arch), tempfile.TemporaryDirectory() as temporary:
                env = {"LFS_ARCH": arch, "LFS_BITS": bits, "LFS_TARGET": target,
                       "LFS_SYSROOT": temporary + "/sysroot", "LFS_WORKSPACE": temporary}
                with patch.dict(os.environ, env), \
                     patch.object(package_lib, "archive_source", return_value=Path(temporary)), \
                     patch.object(package_lib, "run_configure") as configure, \
                     patch("subprocess.run"):
                    runpy.run_path(str(ROOT / "src/packages/nspr/build.py"))
                command = configure.call_args.args[0]
                self.assertIn("--host=x86_64-pc-linux-gnu", command)
                self.assertIn("--target=" + target, command)
                self.assertEqual("--enable-64bit" in command, arch == "x64")
                build_env = configure.call_args.kwargs["env"]
                self.assertEqual(build_env["HOST_CC"], "/usr/bin/gcc")
                self.assertEqual(build_env["HOST_LDFLAGS"], "")
                self.assertEqual(build_env["CC"], target + "-gcc")

    def test_nss_keeps_native_tools_separate_and_installs_target_runtime(self):
        for arch, bits, target in (("x86", "32", "i686-lfs-linux-gnu"),
                                   ("x64", "64", "x86_64-lfs-linux-gnu")):
            with self.subTest(arch=arch), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                source = base / "source"
                dist = base / "build/nss-dist"
                (dist / "lfs.OBJ/lib").mkdir(parents=True)
                (dist / "lfs.OBJ/bin").mkdir()
                (dist / "public/nss").mkdir(parents=True)
                for name in ("libnss3.so", "libnssutil3.so", "libsmime3.so", "libsoftokn3.so"):
                    (dist / "lfs.OBJ/lib" / name).write_text("target library")
                (dist / "lfs.OBJ/bin/certutil").write_text("target executable")
                (dist / "public/nss/nss.h").write_text("target header")
                env = {"LFS_ARCH": arch, "LFS_BITS": bits, "LFS_TARGET": target,
                       "LFS_SYSROOT": str(base / "sysroot"), "LFS_WORKSPACE": str(base)}
                with patch.dict(os.environ, env), \
                     patch.object(package_lib, "archive_source", return_value=source), \
                     patch("subprocess.run") as execute:
                    runpy.run_path(str(ROOT / "src/packages/nss/build.py"))
                native, target_build = execute.call_args_list
                self.assertIn("CC=/usr/bin/gcc", native.args[0])
                self.assertEqual(native.kwargs["env"]["LDFLAGS"], "")
                self.assertNotIn(str(base / "sysroot"), " ".join(native.args[0]))
                self.assertIn("CC=" + target + "-gcc --sysroot=" + str(base / "sysroot"), target_build.args[0])
                self.assertIn("NSPR_LIB_DIR=" + str(base / "sysroot/usr/lib"), target_build.args[0])
                self.assertIn("SQLITE_LIB_DIR=" + str(base / "sysroot/usr/lib"), target_build.args[0])
                self.assertEqual("USE_64=1" in target_build.args[0], arch == "x64")
                self.assertTrue((base / "sysroot/usr/lib/libsoftokn3.so").is_file())
                self.assertTrue((base / "sysroot/usr/include/nss/nss.h").is_file())
                self.assertTrue((base / "sysroot/usr/bin/certutil").is_file())
                self.assertNotIn(temporary, (base / "sysroot/usr/lib/pkgconfig/nss.pc").read_text())
                # Expand the recipe's override with GNU make's assignment rules.
                # This target prints link flags and performs no compilation.
                makefile = base / "link-flags.mk"
                makefile.write_text(
                    "OS_PTHREAD = -lpthread\n"
                    "OS_LIBS = $(OS_PTHREAD) -ldl -lc\n"
                    "ZLIB_LIBS = -lz\n"
                    "OS_LIBS += $(ZLIB_LIBS)\n"
                    ".PHONY: inspect\n"
                    "inspect:\n\t@printf '%s\\n' '-lsqlite3 $(OS_LIBS)'\n"
                )
                override = next(arg for arg in target_build.args[0] if arg.startswith("OS_LIBS="))
                result = subprocess.run(
                    ["make", "--no-print-directory", "-f", str(makefile), "inspect", override],
                    capture_output=True, text=True, check=True,
                )
                libraries = result.stdout.split()
                self.assertIn("-lz", libraries)
                self.assertLess(libraries.index("-lsqlite3"), libraries.index("-lm"))
                self.assertIn("-lpthread", libraries)

    def test_cups_requires_shared_client_library_and_target_tls(self):
        with patch.object(package_lib, "archive_source", return_value=Path("source")), \
             patch("subprocess.run"), \
             patch.object(package_lib, "configure_make_install") as configure:
            runpy.run_path(str(ROOT / "src/packages/cups/build.py"))
        options = configure.call_args.kwargs["options"]
        self.assertIn("--with-components=libcups", options)
        self.assertIn("--enable-shared", options)
        self.assertIn("--with-tls=openssl", options)
        self.assertIn("--libdir=/usr/lib", options)


if __name__ == "__main__":
    unittest.main()
