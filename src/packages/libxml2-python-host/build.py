import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source(
    "libxml2-python-host", "libxml2-2.13.8.tar.xz", "libxml2-2.13.8"
)
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env = os.environ.copy()
env.update(
    {
        "CC": "gcc",
        "CXX": "g++",
        "CFLAGS": "-O2 -std=gnu11",
        "CPPFLAGS": "",
        "LDFLAGS": "",
        "PYTHON": str(tools / "bin/python3"),
        "PATH": str(tools / "bin") + ":/usr/bin:/bin",
        "LD_LIBRARY_PATH": str(tools / "lib"),
    }
)
for name in ("PKG_CONFIG_SYSROOT_DIR", "PKG_CONFIG_LIBDIR", "PKG_CONFIG_PATH"):
    env.pop(name, None)
env["PKG_CONFIG_PATH"] = ":".join(
    (str(tools / "lib/pkgconfig"), str(tools / "share/pkgconfig"))
)
run_configure(
    [
        str(source / "configure"),
        "--prefix=" + str(tools),
        "--libdir=" + str(tools / "lib"),
        "--with-python",
        "--with-python-sys-prefix",
        "--disable-static",
    ],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
