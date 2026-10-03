import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source, environment

source = archive_source("screen", "screen-5.0.1.tar.gz", "screen-5.0.1")
env = environment()
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + env.get("LFS_TARGET", "i686-lfs-linux-gnu"),
        "--prefix=/usr",
        "--sysconfdir=/etc",
        "--enable-pam",
        "--with-system_screenrc=/etc/screenrc",
    ],
    cwd=source,
    env=env,
    check=True,
)
# Rebuild all generated objects with the target compiler.
subprocess.run(["make", "clean"], cwd=source, env=env, check=True)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
dest = "DESTDIR=" + os.environ["LFS_SYSROOT"]
# ncurses supplies terminfo; installation must not invoke the host tic.
subprocess.run(["make", dest, "install_bin"], cwd=source, env=env, check=True)
subprocess.run(["make", "-C", "doc", dest, "install"], cwd=source, env=env, check=True)
# PAM authentication uses unix_chkpwd; screen runs without set-user-ID.
(Path(os.environ["LFS_SYSROOT"]) / "usr/bin/screen-5.0.1").chmod(0o755)
