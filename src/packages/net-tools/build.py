import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("net-tools", "net-tools-2.10.tar.xz", "net-tools-2.10")
sysroot = Path(os.environ["LFS_SYSROOT"])
env = environment()
subprocess.run(
    ["bash", "configure.sh", "config.in"],
    cwd=source,
    env=env,
    input="\n" * 100,
    text=True,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(
    [
        "make",
        "DESTDIR=" + str(sysroot),
        "BINDIR=/usr/bin",
        "SBINDIR=/usr/sbin",
        "install",
    ],
    cwd=source,
    env=env,
    check=True,
)
