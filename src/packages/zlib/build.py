import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
import subprocess
from package_lib import archive_source, environment

source = archive_source("zlib", "zlib-1.3.1.tar.gz", "zlib-1.3.1")
env = environment()
env["CHOST"] = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
subprocess.run(
    [str(source / "configure"), "--prefix=/usr", "--static"],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=source,
    env=env,
    check=True,
)
