import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("gcc-bootstrap", "gcc-15.2.0.tar.xz", "gcc-15.2.0")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/gcc-bootstrap"
build.mkdir(parents=True, exist_ok=True)
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
configure = [str(source / "configure"), "--target=i686-lfs-linux-gnu", "--prefix=/usr",
             "--with-sysroot=" + os.environ["LFS_SYSROOT"], "--with-gmp=" + str(tools),
             "--with-mpfr=" + str(tools), "--with-mpc=" + str(tools), "--without-headers",
             "--with-newlib", "--disable-shared", "--disable-threads", "--disable-libssp",
             "--disable-decimal-float", "--disable-libquadmath", "--disable-libvtv",
             "--disable-libgomp", "--disable-libatomic", "--disable-libgcov", "--disable-nls", "--disable-multilib",
             "--enable-languages=c"]
subprocess.run(configure, cwd=build, check=True)
subprocess.run(["make", "-j" + str(os.cpu_count() or 1), "all-gcc"], cwd=build, check=True)
target_env = os.environ.copy()
target_env["CFLAGS_FOR_TARGET"] = "-O2 -g -ffreestanding -fno-stack-protector -Dinhibit_libc"
target_env["CXXFLAGS_FOR_TARGET"] = target_env["CFLAGS_FOR_TARGET"]
subprocess.run(["make", "-j" + str(os.cpu_count() or 1), "all-target-libgcc"], cwd=build, env=target_env, check=True)
subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install-gcc", "install-target-libgcc"], cwd=build, env=target_env, check=True)
