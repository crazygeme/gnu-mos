import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source, environment

source = archive_source("icu", "icu4c-77_1-src.tgz", "icu") / "source"
workspace = Path(os.environ["LFS_WORKSPACE"]).resolve()
tools = workspace / "tools"
host_build = workspace / "build/icu-host"
target_build = workspace / "build/icu-target"
host_build.mkdir(parents=True, exist_ok=True)
target_build.mkdir(parents=True, exist_ok=True)

host_env = os.environ.copy()
host_env.update(
    {
        "CC": "gcc",
        "CXX": "g++",
        "AR": "ar",
        "AS": "as",
        "LD": "ld",
        "NM": "nm",
        "RANLIB": "ranlib",
        "STRIP": "strip",
        "CFLAGS": "-O2",
        "CXXFLAGS": "-O2",
        "CPPFLAGS": "",
        "LDFLAGS": "",
        "PATH": str(tools / "bin") + ":/usr/bin:/bin",
    }
)
for name in (
    "PKG_CONFIG_SYSROOT_DIR",
    "PKG_CONFIG_LIBDIR",
    "PKG_CONFIG_PATH",
    "LD_LIBRARY_PATH",
    "LIBRARY_PATH",
    "CPATH",
    "C_INCLUDE_PATH",
    "CPLUS_INCLUDE_PATH",
    "CONFIG_SITE",
):
    host_env.pop(name, None)

options = ("--disable-static", "--disable-tests", "--disable-samples")
run_configure(
    [str(source / "configure"), "--prefix=" + str(tools), *options],
    cwd=host_build,
    env=host_env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=host_build, env=host_env, check=True)

target_env = environment()
target = target_env.get("LFS_TARGET", "i686-lfs-linux-gnu")
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + target,
        "--prefix=/usr",
        "--libdir=/usr/lib",
        "--with-cross-build=" + str(host_build),
        *options,
    ],
    cwd=target_build,
    env=target_env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=target_build, env=target_env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=target_build,
    env=target_env,
    check=True,
)
