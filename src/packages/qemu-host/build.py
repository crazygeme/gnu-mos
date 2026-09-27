import hashlib
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

workspace = Path(os.environ["LFS_WORKSPACE"])
archive = Path(os.environ["LFS_SOURCES"]) / "qemu-10.2.1.tar.xz"
with archive.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
if digest != "a3717477d8e2c84d630bfffbc20f6cd3293eb45aa1e6dac6d0cc27689991c9e1":
    raise RuntimeError("QEMU source archive SHA-256 mismatch")

env = os.environ.copy()
for key in (
    "CC", "CXX", "AR", "AS", "LD", "RANLIB", "STRIP", "NM",
    "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "LD_LIBRARY_PATH",
    "PKG_CONFIG", "PKG_CONFIG_PATH", "PKG_CONFIG_LIBDIR",
    "PKG_CONFIG_SYSROOT_DIR", "PYTHONPATH", "DESTDIR",
):
    env.pop(key, None)
env["PATH"] = f"{workspace / 'tools/bin'}:/usr/bin:/bin"
env.update(CC="gcc", CXX="g++", CFLAGS="-O2", CXXFLAGS="-O2")
subprocess.run(
    ["pkg-config", "--print-errors", "--exists", "glib-2.0", "gio-2.0",
     "pixman-1", "epoxy", "sdl2", "virglrenderer", "gbm", "libdrm", "zlib"],
    env=env, check=True,
)
source = archive_source(
    "qemu-host", archive.name, "qemu-10.2.1",
    excluded_members=(
        "qemu-10.2.1/roms/edk2/EmulatorPkg/Unix/Host/X11IncludeHack",
    ),
)
for patch_name in ("sdl-gl-scanout.patch", "sdl-relative-pointer.patch"):
    patch = Path(__file__).with_name(patch_name)
    for options in (("--dry-run",), ()):
        subprocess.run(
            ["patch", "--batch", "-p1", *options, "-i", str(patch)],
            cwd=source, env=env, check=True,
        )
build = workspace / "build/qemu-host-build"
build.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [str(source / "configure"),
     "--prefix=" + str(workspace / "tools/qemu"),
     "--target-list=x86_64-softmmu", "--python=" + sys.executable,
     "--enable-kvm", "--enable-sdl", "--enable-opengl",
     "--enable-virglrenderer", "--enable-pixman",
     "--disable-docs", "--disable-werror"],
    cwd=build, env=env, check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(["make", "install"], cwd=build, env=env, check=True)
