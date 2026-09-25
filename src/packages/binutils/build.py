import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("binutils", "binutils-2.45.tar.xz", "binutils-2.45")
workspace = Path(os.environ["LFS_WORKSPACE"])
build = workspace / "build/binutils"
tools = workspace / "tools"
build.mkdir(parents=True, exist_ok=True)
patch_file = Path(__file__).with_name("gprofng-glibc-strstr.patch")
subprocess.run(
    ["patch", "-p1", "--forward", "--batch", "-i", str(patch_file)],
    cwd=source,
    check=True,
)
subprocess.run(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--target=i686-lfs-linux-gnu",
        "--prefix=/",
        "--disable-nls",
        "--disable-werror",
    ],
    cwd=build,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, check=True)
subprocess.run(["make", "DESTDIR=" + str(tools), "install"], cwd=build, check=True)
