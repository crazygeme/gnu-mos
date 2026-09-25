import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("gmp-target", "gmp-6.3.0.tar.xz", "gmp-6.3.0")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/gmp-target"
build.mkdir(parents=True, exist_ok=True)
env = environment()
env["CFLAGS"] = "-O2 -m32 -std=gnu11"
env["ABI"] = "32"
env.pop("LD_LIBRARY_PATH", None)
subprocess.run(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + env["LFS_TARGET"],
        "--prefix=/usr",
        "--disable-shared",
        "--enable-static",
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=build,
    env=env,
    check=True,
)
(Path(os.environ["LFS_SYSROOT"]) / "usr/lib/libgmp.la").unlink(missing_ok=True)
