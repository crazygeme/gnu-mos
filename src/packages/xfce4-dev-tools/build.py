import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source(
    "xfce4-dev-tools", "xfce4-dev-tools-4.20.0.tar.bz2", "xfce4-dev-tools-4.20.0"
)
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env = os.environ.copy()
env.update(
    {
        "CC": "gcc",
        "CXX": "g++",
        "AR": "ar",
        "RANLIB": "ranlib",
        "LD": "ld",
        "CFLAGS": "-O2",
        "CXXFLAGS": "-O2",
        "CPPFLAGS": "",
        "LDFLAGS": "",
        "PATH": f"{tools / 'bin'}:/usr/bin:/bin",
        "LD_LIBRARY_PATH": str(tools / "lib"),
        "PKG_CONFIG": "/usr/bin/pkg-config",
        "PKG_CONFIG_PATH": f"{tools / 'lib/pkgconfig'}:{tools / 'share/pkgconfig'}",
    }
)
for name in ("PKG_CONFIG_SYSROOT_DIR", "PKG_CONFIG_LIBDIR"):
    env.pop(name, None)
run_configure(
    [str(source / "configure"), "--prefix=" + str(tools)],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
