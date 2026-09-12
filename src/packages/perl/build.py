import os, subprocess, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[2]))
from package_lib import archive_source
source = archive_source("perl", "perl-5.42.0.tar.xz", "perl-5.42.0")
env = os.environ.copy()
env["CC"] = env.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-gcc"
env["CFLAGS"] = "-O2 -m32"
subprocess.run([str(source / "Configure"), "-des", "-Dprefix=/usr", "-Duseshrplib"], cwd=source, env=env, check=True)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=source, env=env, check=True)
subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=source, env=env, check=True)
