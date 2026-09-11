import os, subprocess
from pathlib import Path
source = Path(os.environ["LFS_SOURCES"]) / "glibc-2.42"; build = Path(os.environ["LFS_WORKSPACE"]) / "build/glibc"; build.mkdir(parents=True, exist_ok=True)
subprocess.run([str(source / "configure"), "--prefix=/usr", "--host=i686-lfs-linux-gnu", "--disable-werror", "--with-headers=" + str(Path(os.environ["LFS_SYSROOT"]) / "usr/include")], cwd=build, check=True)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=build, check=True)
subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=build, check=True)
