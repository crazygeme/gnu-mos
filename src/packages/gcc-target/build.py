import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

workspace = Path(os.environ["LFS_WORKSPACE"])
sysroot = Path(os.environ["LFS_SYSROOT"])
tools = workspace / "tools"
tools_bin = tools / "bin"
target = os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu")
source = archive_source("gcc-target", "gcc-15.2.0.tar.xz", "gcc-15.2.0")
build = workspace / "build/gcc-target"
build.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update(
    {
        "CC": target + "-gcc",
        "CXX": target + "-g++",
        "CC_FOR_BUILD": "gcc",
        "CXX_FOR_BUILD": "g++",
        "CFLAGS": "-O2",
        "CXXFLAGS": "-O2",
        "PATH": ":".join((str(tools_bin), "/usr/bin", "/bin")),
        "CONFIG_SHELL": "/bin/bash",
        "SHELL": "/bin/bash",
        "INSTALL": "/usr/bin/install",
    }
)
for n in (
    "LD_LIBRARY_PATH",
    "LIBRARY_PATH",
    "CPATH",
    "C_INCLUDE_PATH",
    "CPLUS_INCLUDE_PATH",
):
    env.pop(n, None)
configure = [
    str(source / "configure"),
    "--build=x86_64-pc-linux-gnu",
    "--host=" + target,
    "--target=" + target,
    "--prefix=/usr",
    "--with-build-sysroot=" + str(sysroot),
    "--with-gmp=" + str(sysroot / "usr"),
    "--with-mpfr=" + str(sysroot / "usr"),
    "--with-mpc=" + str(sysroot / "usr"),
    "--with-native-system-header-dir=/usr/include",
    "--disable-nls",
    "--disable-multilib",
    "--enable-languages=c,c++",
]
subprocess.run(configure, cwd=build, env=env, check=True)
subprocess.run(
    [
        "make",
        "-j4",
        "CFLAGS_FOR_TARGET=-O2 -m32",
        "CXXFLAGS_FOR_TARGET=-O2 -m32",
        "all-target-libgcc",
        "all-target-libstdc++-v3",
        "all-gcc",
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(
    [
        "make",
        "DESTDIR=" + str(sysroot),
        "install-target-libgcc",
        "install-target-libstdc++-v3",
        "install-gcc",
    ],
    cwd=build,
    env=env,
    check=True,
)
