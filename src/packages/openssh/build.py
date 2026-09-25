import os, subprocess, tarfile
from pathlib import Path

w = Path(os.environ["LFS_WORKSPACE"])
s = Path(os.environ["LFS_SOURCES"])
root = Path(os.environ["LFS_SYSROOT"])
src = w / "build/openssh-10.0p1"
if not src.exists():
    with tarfile.open(s / "openssh-10.0p1.tar.gz") as f:
        f.extractall(w / "build", filter="data")
env = os.environ.copy()
env.update(
    {
        "CC": "i686-lfs-linux-gnu-gcc",
        "AR": "i686-lfs-linux-gnu-ar",
        "RANLIB": "i686-lfs-linux-gnu-ranlib",
        "STRIP": "i686-lfs-linux-gnu-strip",
        "CFLAGS": "-O2 -m32",
        "LDFLAGS": "--sysroot=" + str(root) + " -no-pie",
        "PATH": "/usr/bin:/bin:" + env.get("PATH", ""),
    }
)
subprocess.run(
    [
        str(src / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=i686-lfs-linux-gnu",
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
