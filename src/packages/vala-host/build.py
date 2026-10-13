import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, run_configure

workspace = Path(os.environ["LFS_WORKSPACE"])
tools = workspace / "tools"
source = archive_source("vala-host", "vala-0.56.18.tar.xz", "vala-0.56.18")
env = os.environ.copy()
for variable in (
    "CC", "CXX", "AR", "AS", "LD", "RANLIB", "STRIP", "NM", "CFLAGS", "CXXFLAGS",
    "CPPFLAGS", "LDFLAGS", "LD_LIBRARY_PATH", "LIBRARY_PATH", "CPATH", "PKG_CONFIG",
    "PKG_CONFIG_PATH", "PKG_CONFIG_LIBDIR", "PKG_CONFIG_SYSROOT_DIR", "PYTHONPATH", "DESTDIR",
    "GI_GIRDIR",
):
    env.pop(variable, None)
env.update(
    PATH=f"{tools / 'bin'}:/usr/bin:/bin", CC="gcc", CXX="g++",
    CFLAGS="-O2 -std=gnu17", VALAC="/usr/bin/valac",
    PKG_CONFIG_PATH=f"{tools / 'lib/pkgconfig'}:{tools / 'share/pkgconfig'}",
    LD_LIBRARY_PATH=str(tools / "lib"),
)
run_configure(
    [str(source / "configure"), "--prefix=" + str(tools), "--libdir=" + str(tools / "lib"),
     "--enable-unversioned", "--disable-valadoc"],
    cwd=source, env=env, check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
