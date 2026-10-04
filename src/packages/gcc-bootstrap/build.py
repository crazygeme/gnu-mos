import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source("gcc-bootstrap", "gcc-15.2.0.tar.xz", "gcc-15.2.0")
workspace = Path(os.environ["LFS_WORKSPACE"])
build = workspace / "build/gcc-bootstrap"
tools = workspace / "tools"
tools_bin = tools / "bin"
build.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update(
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
    env.pop(name, None)
configure = [
    str(source / "configure"),
    "--build=x86_64-pc-linux-gnu",
    "--host=x86_64-pc-linux-gnu",
    "--target=" + os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu"),
    "--prefix=/",
    "--with-sysroot=" + os.environ["LFS_SYSROOT"],
    "--with-gmp=" + str(tools),
    "--with-mpfr=" + str(tools),
    "--with-mpc=" + str(tools),
    "--with-as="
    + str(tools_bin / (os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-as")),
    "--with-ld="
    + str(tools_bin / (os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ld")),
    "--without-headers",
    "--with-newlib",
    "--disable-shared",
    "--disable-threads",
    "--disable-libssp",
    "--disable-nls",
    "--disable-multilib",
    "--enable-languages=c",
]
run_configure(configure, cwd=build, env=env, check=True)
subprocess.run(
    ["make", "-j4", "all-gcc", "all-target-libgcc"], cwd=build, env=env, check=True
)
subprocess.run(
    ["make", "DESTDIR=" + str(tools), "install-gcc", "install-target-libgcc"],
    cwd=build,
    env=env,
    check=True,
)
