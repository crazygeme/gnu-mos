import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source, environment

source = archive_source("mpfr-target", "mpfr-4.2.2.tar.xz", "mpfr-4.2.2")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/mpfr-target"
build.mkdir(parents=True, exist_ok=True)
sysroot = Path(os.environ["LFS_SYSROOT"])
env = environment()
env.pop("LD_LIBRARY_PATH", None)
(sysroot / "usr/lib/libgmp.la").unlink(missing_ok=True)
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + env["LFS_TARGET"],
        "--prefix=/usr",
        "--disable-shared",
        "--enable-static",
        "--with-gmp-include=" + str(sysroot / "usr/include"),
        "--with-gmp-lib=" + str(sysroot / "usr/lib"),
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + str(sysroot), "install"], cwd=build, env=env, check=True
)
(sysroot / "usr/lib/libmpfr.la").unlink(missing_ok=True)
