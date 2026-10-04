import os, subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source
from package_lib import environment

source = archive_source("glibc", "glibc-2.42.tar.xz", "glibc-2.42")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/glibc"
build.mkdir(parents=True, exist_ok=True)
env = environment()
env["CFLAGS"] = "-O2 -m" + os.environ.get("LFS_BITS", "32")
options = []
if os.environ.get("LFS_ARCH") == "x64":
    env["libc_cv_slibdir"] = "/usr/lib"
    options = ["--libdir=/usr/lib"]
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu"),
        "--prefix=/usr",
        "--disable-werror",
        *options,
        "--with-headers=" + str(Path(os.environ["LFS_SYSROOT"]) / "usr/include"),
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, check=True)
subprocess.run(
    ["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=build,
    env=env,
    check=True,
)
