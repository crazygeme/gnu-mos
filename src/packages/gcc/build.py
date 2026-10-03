import os, subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source("gcc", "gcc-15.2.0.tar.xz", "gcc-15.2.0")
workspace = Path(os.environ["LFS_WORKSPACE"])
build = workspace / "build/gcc-final"
tools = workspace / "tools"
tools_bin = tools / "bin"
build.mkdir(parents=True, exist_ok=True)
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
target_bin = tools_bin
build_env = os.environ.copy()
build_env.update(
    {
        "PATH": ":".join((str(tools_bin), "/usr/bin", "/bin")),
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
    "--prefix=/",
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
run_configure(configure, cwd=build, env=build_env, check=True)
subprocess.run(
    [
        "make",
        "-j4",
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
        "DESTDIR=" + str(tools),
        "install-target-libgcc",
        "install-target-libstdc++-v3",
        "install-gcc",
    ],
    cwd=build,
    env=build_env,
    check=True,
)
