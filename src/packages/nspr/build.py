import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment, run_configure

source = archive_source("nspr", "nspr-4.38.2.tar.gz", "nspr-4.38.2") / "nspr"
env = environment()
env.update(HOST_CC="/usr/bin/gcc", HOST_CFLAGS="-O2", HOST_LDFLAGS="")
# NSPR uses --target for the library ABI and --host for native build tools.
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=x86_64-pc-linux-gnu",
        "--target=" + env["LFS_TARGET"],
        "--prefix=/usr",
        "--libdir=/usr/lib",
        "--includedir=/usr/include/nspr",
        "--disable-debug",
        "--enable-optimize",
        *(["--enable-64bit"] if env["LFS_ARCH"] == "x64" else []),
    ],
    cwd=source,
    env=env,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + env["LFS_SYSROOT"], "install"],
    cwd=source, env=env, check=True,
)
