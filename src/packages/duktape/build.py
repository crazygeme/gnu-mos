import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("duktape", "duktape-2.7.0.tar.xz", "duktape-2.7.0")
env = environment()
command = [
    "make", "-f", "Makefile.sharedlibrary",
    "CC=" + env["CC"], "INSTALL_PREFIX=/usr", "LIBDIR=/lib",
]
subprocess.run([*command, "-j4"], cwd=source, env=env, check=True)
subprocess.run(
    [*command, "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=source, env=env, check=True,
)
