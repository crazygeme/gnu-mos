import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

workspace = Path(os.environ["LFS_WORKSPACE"])
prefix = workspace / "tools/virglrenderer"
source = archive_source(
    "virglrenderer-host", "virglrenderer-1.3.0.tar.bz2", "virglrenderer-1.3.0"
)
build = workspace / "build/virglrenderer-host"
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
    [
        "meson", "setup", str(build), str(source),
        "--prefix=" + str(prefix), "--libdir=lib",
        "--buildtype=release", "-Dplatforms=egl,glx", "-Dvideo=true",
        "-Dunstable-apis=true",
    ],
    env=env,
    check=True,
)
subprocess.run(["meson", "compile", "-C", str(build)], env=env, check=True)
subprocess.run(["meson", "install", "-C", str(build)], env=env, check=True)
