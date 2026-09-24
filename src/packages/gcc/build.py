import os, subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("gcc", "gcc-15.2.0.tar.xz", "gcc-15.2.0")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/gcc-final"
build.mkdir(parents=True, exist_ok=True)
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
target_bin = Path(os.environ["LFS_SYSROOT"]) / "usr/bin"
build_env = os.environ.copy()
build_env.update(
    {
        "PATH": ":".join((str(tools / "bin"), "/usr/bin", "/bin", str(target_bin))),
        "CONFIG_SHELL": "/bin/bash",
        "SHELL": "/bin/bash",
        "INSTALL": "/usr/bin/install",
    }
)
for name in (
    "LD_LIBRARY_PATH",
    "LIBRARY_PATH",
    "CPATH",
    "C_INCLUDE_PATH",
    "CPLUS_INCLUDE_PATH",
):
    build_env.pop(name, None)
configure = [
    str(source / "configure"),
    "--target=i686-lfs-linux-gnu",
    "--prefix=/usr",
    "--with-sysroot=" + os.environ["LFS_SYSROOT"],
    "--with-gmp=" + str(tools),
    "--with-mpfr=" + str(tools),
    "--with-mpc=" + str(tools),
    "--with-as=" + str(target_bin / "i686-lfs-linux-gnu-as"),
    "--with-ld=" + str(target_bin / "i686-lfs-linux-gnu-ld"),
    "--disable-nls",
    "--disable-multilib",
    "--enable-languages=c,c++",
]
subprocess.run(configure, cwd=build, env=build_env, check=True)
subprocess.run(
    [
        "make",
        "-j" + str(os.cpu_count() or 1),
        "all-target-libgcc",
        "all-target-libstdc++-v3",
        "all-gcc",
    ],
    cwd=build,
    env=build_env,
    check=True,
)
subprocess.run(
    [
        "make",
        "DESTDIR=" + os.environ["LFS_SYSROOT"],
        "install-target-libgcc",
        "install-target-libstdc++-v3",
        "install-gcc",
    ],
    cwd=build,
    env=build_env,
    check=True,
)
