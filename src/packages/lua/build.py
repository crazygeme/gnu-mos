import os
import subprocess
import tarfile
from pathlib import Path

workspace = Path(os.environ["LFS_WORKSPACE"])
sources = Path(os.environ["LFS_SOURCES"])
sysroot = Path(os.environ["LFS_SYSROOT"])
source = workspace / "build/lua-5.4.8"

if not source.exists():
    with tarfile.open(sources / "lua-5.4.8.tar.gz") as package:
        package.extractall(workspace / "build", filter="data")

environment = os.environ.copy()
environment.update(
    {
        "CC": "i686-lfs-linux-gnu-gcc",
        "AR": "i686-lfs-linux-gnu-ar",
        "RANLIB": "i686-lfs-linux-gnu-ranlib",
        "MYCFLAGS": "-O2 -m32 -fPIC",
        "MYLDFLAGS": "-m32",
    }
)

subprocess.run(
    ["make", "-j4", "linux"],
    cwd=source,
    env=environment,
    check=True,
)
subprocess.run(
    ["make", "INSTALL_TOP=" + str(sysroot / "usr"), "install"],
    cwd=source,
    env=environment,
    check=True,
)
