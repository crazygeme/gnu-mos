import os, subprocess
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source
source = archive_source("gcc", "gcc-15.2.0.tar.xz", "gcc-15.2.0"); build = Path(os.environ["LFS_WORKSPACE"]) / "build/gcc"; build.mkdir(parents=True, exist_ok=True)
subprocess.run([str(source / "configure"), "--target=i686-lfs-linux-gnu", "--prefix=/usr", "--with-sysroot=" + os.environ["LFS_SYSROOT"], "--disable-nls", "--disable-multilib", "--enable-languages=c,c++"], cwd=build, check=True)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=build, check=True)
subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=build, check=True)
