import os, subprocess
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source
source = archive_source("glibc", "glibc-2.42.tar.xz", "glibc-2.42"); build = Path(os.environ["LFS_WORKSPACE"]) / "build/glibc"; build.mkdir(parents=True, exist_ok=True)
subprocess.run([str(source / "configure"), "--prefix=/usr", "--host=i686-lfs-linux-gnu", "--disable-werror", "--with-headers=" + str(Path(os.environ["LFS_SYSROOT"]) / "usr/include")], cwd=build, check=True)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=build, check=True)
subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=build, check=True)
