import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source, environment

source = archive_source("file", "file-5.46.tar.gz", "file-5.46")
native = source / "build-native"
target_build = source / "build-target"
native.mkdir()
target_build.mkdir()

# The magic database compiler must match the target package version.
host_env = os.environ.copy()
host_env.update({
    "PATH": "/usr/bin:/bin", "CC": "gcc", "CXX": "g++",
    "AR": "ar", "RANLIB": "ranlib", "LD": "ld", "STRIP": "strip",
    "CFLAGS": "-O2", "CXXFLAGS": "-O2", "CPPFLAGS": "", "LDFLAGS": "",
})
for variable in ("LD_LIBRARY_PATH", "PKG_CONFIG_SYSROOT_DIR", "PKG_CONFIG_LIBDIR"):
    host_env.pop(variable, None)
run_configure([str(source / "configure")], cwd=native, env=host_env, check=True)
subprocess.run(["make", "-j4"], cwd=native, env=host_env, check=True)

env = environment()
target = os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu")
run_configure(
    [str(source / "configure"), "--build=x86_64-pc-linux-gnu",
     "--host=" + target, "--prefix=/usr", "--enable-zlib",
     "--enable-bzlib", "--enable-xzlib"],
    cwd=target_build, env=env, check=True,
)
compiler = "FILE_COMPILE=" + str(native / "src/file")
subprocess.run(["make", "-j4", compiler], cwd=target_build, env=env, check=True)
sysroot = Path(os.environ["LFS_SYSROOT"])
subprocess.run(
    ["make", "DESTDIR=" + str(sysroot), compiler, "install"],
    cwd=target_build, env=env, check=True,
)
(sysroot / "usr/lib/libmagic.la").unlink(missing_ok=True)
