import os, subprocess, tarfile
from pathlib import Path

w = Path(os.environ["LFS_WORKSPACE"])
src = w / "build/netsurf-all-3.11"
if not src.exists():
    with tarfile.open(Path(os.environ["LFS_SOURCES"]) / "netsurf-all-3.11.tar.gz") as f:
        f.extractall(w / "build", filter="data")
env = os.environ.copy()
env.update(
    {
        "TARGET": "gtk",
        "CC": "i686-lfs-linux-gnu-gcc",
        "AR": "i686-lfs-linux-gnu-ar",
        "RANLIB": "i686-lfs-linux-gnu-ranlib",
        "CFLAGS": "-O2 -m32",
    }
)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=src, env=env, check=True)
subprocess.run(
    ["make", "install", "PREFIX=/usr", "DESTDIR=" + os.environ["LFS_SYSROOT"]],
    cwd=src,
    env=env,
    check=True,
)
