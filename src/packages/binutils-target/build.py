import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("binutils-target", "binutils-2.45.tar.xz", "binutils-2.45")
subprocess.run(
    ["patch", "-p1", "--forward", "--batch", "-i",
     str(Path(__file__).with_name("gprofng-glibc-strstr.patch"))],
    cwd=source,
    check=True,
)
workspace = Path(os.environ["LFS_WORKSPACE"])
sysroot = Path(os.environ["LFS_SYSROOT"])
target = os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu")
build = workspace / "build/binutils-target"
build.mkdir(parents=True, exist_ok=True)
env = environment()
env.update({"CC_FOR_BUILD": "gcc", "CXX_FOR_BUILD": "g++"})
subprocess.run(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + target,
        "--target=" + target,
        "--prefix=/usr",
        "--with-sysroot=/",
        "--disable-nls",
        "--disable-werror",
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + str(sysroot), "install"],
    cwd=build,
    env=env,
    check=True,
)
