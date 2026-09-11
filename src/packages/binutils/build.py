import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source
source = archive_source("binutils", "binutils-2.45.tar.xz", "binutils-2.45")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/binutils"
build.mkdir(parents=True, exist_ok=True)
subprocess.run([str(source / "configure"), "--target=i686-lfs-linux-gnu", "--prefix=/usr", "--disable-nls", "--disable-werror"], cwd=build, check=True)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=build, check=True)
subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=build, check=True)
