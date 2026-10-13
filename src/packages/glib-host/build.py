import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

workspace = Path(os.environ["LFS_WORKSPACE"])
tools = workspace / "tools"
source = archive_source("glib-host", "glib-2.88.1.tar.xz", "glib-2.88.1")
build = workspace / "build/glib-host"
env = os.environ.copy()
for variable in (
    "CC", "CXX", "AR", "AS", "LD", "RANLIB", "STRIP", "NM", "CFLAGS", "CXXFLAGS",
    "CPPFLAGS", "LDFLAGS", "LD_LIBRARY_PATH", "LIBRARY_PATH", "CPATH", "PKG_CONFIG",
    "PKG_CONFIG_PATH", "PKG_CONFIG_LIBDIR", "PKG_CONFIG_SYSROOT_DIR", "PYTHONPATH", "DESTDIR",
):
    env.pop(variable, None)
env.update(
    PATH=f"{tools / 'bin'}:/usr/bin:/bin", CC="gcc", CXX="g++", CFLAGS="-O2",
    PKG_CONFIG_PATH=f"{tools / 'lib/pkgconfig'}:{tools / 'share/pkgconfig'}",
    LD_LIBRARY_PATH=str(tools / "lib"),
)
# Introspection data generation depends on the scanner built with this GLib.
subprocess.run(
    ["meson", "setup", str(build), str(source), "--prefix=" + str(tools), "--libdir=lib",
     "--wrap-mode=nofallback", "-Dtests=false", "-Dintrospection=disabled"],
    env=env, check=True,
)
subprocess.run(["meson", "compile", "-C", str(build)], env=env, check=True)
subprocess.run(["meson", "install", "-C", str(build)], env=env, check=True)
