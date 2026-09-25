import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("libcap", "libcap-2.76.tar.xz", "libcap-2.76")
env = environment()
make_vars = (
    "CROSS_COMPILE=" + env.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-",
    "BUILD_CC=cc",
    "prefix=/usr",
    "lib=lib",
    "LDFLAGS=" + env["LDFLAGS"],
)
subprocess.run(
    ["make", "-C", "libcap", "-j4", *make_vars, "all"],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(
    [
        "make",
        "-C",
        "libcap",
        *make_vars,
        "DESTDIR=" + os.environ["LFS_SYSROOT"],
        "install",
    ],
    cwd=source,
    env=env,
    check=True,
)
