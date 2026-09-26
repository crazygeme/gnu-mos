import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("scron", "scron-0.4.tar.gz", "scron-0.4")
env = environment()
args = ["CC=" + env["CC"], "PREFIX=/usr", "MANPREFIX=/usr/share/man"]
subprocess.run(["make", "-j4", *args], cwd=source, env=env, check=True)
subprocess.run(
    ["make", *args, "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=source, env=env, check=True,
)
