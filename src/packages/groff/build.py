import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source, environment

source = archive_source("groff", "groff-1.23.0.tar.gz", "groff-1.23.0")
sysroot = Path(os.environ["LFS_SYSROOT"])
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools/bin"
env = environment()
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu"),
        "--prefix=/usr",
        "--without-x",
        "--with-uchardet=no",
    ],
    cwd=source,
    env=env,
    check=True,
)
# Build documentation with native tools while installing target executables.
make = ["make", "GROFFBIN=" + str(tools / "groff"), "GROFF_BIN_PATH=" + str(tools)]
subprocess.run([*make, "-j4"], cwd=source, env=env, check=True)
subprocess.run(
    [*make, "DESTDIR=" + str(sysroot), "install"], cwd=source, env=env, check=True
)
