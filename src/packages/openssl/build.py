import os, subprocess, tarfile
from pathlib import Path

w = Path(os.environ["LFS_WORKSPACE"])
s = Path(os.environ["LFS_SOURCES"])
root = Path(os.environ["LFS_SYSROOT"])
src = w / "build/openssl-3.5.2"
if not src.exists():
    with tarfile.open(s / "openssl-3.5.2.tar.gz") as f:
        f.extractall(w / "build", filter="data")
env = os.environ.copy()
env.update(
    {
        "CC": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-gcc",
        "AR": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ar",
        "RANLIB": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ranlib",
        "CFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32"),
        "PERL": "/usr/bin/perl",
        "PATH": "/usr/bin:/bin:" + env.get("PATH", ""),
    }
)
subprocess.run(
    [
        "./Configure",
        "linux-x86_64" if os.environ.get("LFS_ARCH") == "x64" else "linux-generic32",
        *(["--libdir=lib"] if os.environ.get("LFS_ARCH") == "x64" else []),
        "--prefix=/usr",
        "--openssldir=/etc/ssl",
        "shared",
    ],
    cwd=src,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=src, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + str(root), "install_sw"], cwd=src, env=env, check=True
)
