import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

root = Path(os.environ["LFS_SYSROOT"])
src = archive_source("openssh", "openssh-10.0p1.tar.gz", "openssh-10.0p1")
env = os.environ.copy()
env.update(
    {
        "CC": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-gcc",
        "AR": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ar",
        "RANLIB": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ranlib",
        "STRIP": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-strip",
        "CFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32"),
        "LDFLAGS": "--sysroot=" + str(root) + " -no-pie",
        "PATH": "/usr/bin:/bin:" + env.get("PATH", ""),
    }
)
run_configure(
    [
        str(src / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu"),
        "--prefix=/usr",
        "--sysconfdir=/etc/ssh",
        "--disable-strip",
        "--without-pam",
        "--without-pie",
    ],
    cwd=src,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=src, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + str(root), "install"], cwd=src, env=env, check=True
)
