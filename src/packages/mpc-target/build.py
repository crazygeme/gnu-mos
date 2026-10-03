import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source, environment

source = archive_source("mpc-target", "mpc-1.3.1.tar.gz", "mpc-1.3.1")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/mpc-target"
build.mkdir(parents=True, exist_ok=True)
sysroot = Path(os.environ["LFS_SYSROOT"])
env = environment()
env.pop("LD_LIBRARY_PATH", None)
for archive in ("libgmp.la", "libmpfr.la"):
    (sysroot / "usr/lib" / archive).unlink(missing_ok=True)
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
        "--with-mpfr-include=" + str(sysroot / "usr/include"),
        "--with-mpfr-lib=" + str(sysroot / "usr/lib"),
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + str(sysroot), "install"], cwd=build, env=env, check=True
)
(sysroot / "usr/lib/libmpc.la").unlink(missing_ok=True)
