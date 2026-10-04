import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("bzip2", "bzip2-1.0.8.tar.gz", "bzip2-1.0.8")
root = Path(os.environ["LFS_SYSROOT"])
env = os.environ.copy()
env.update(
    {
        "CC": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-gcc",
        "AR": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ar",
        "RANLIB": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ranlib",
        "CFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -fPIC",
    }
)
subprocess.run(
    [
        "make",
        "-j4",
        "CC=" + env["CC"],
        "AR=" + env["AR"],
        "RANLIB=" + env["RANLIB"],
        "CFLAGS=" + env["CFLAGS"],
        "libbz2.a",
    ],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(
    ["install", "-Dm644", "libbz2.a", str(root / "usr/lib/libbz2.a")],
    cwd=source,
    check=True,
)
subprocess.run(
    ["install", "-Dm644", "bzlib.h", str(root / "usr/include/bzlib.h")],
    cwd=source,
    check=True,
)
