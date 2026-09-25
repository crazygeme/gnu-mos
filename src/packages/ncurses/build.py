import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("ncurses", "ncurses-6.5.tar.gz", "ncurses-6.5")
workspace = Path(os.environ["LFS_WORKSPACE"])
sysroot = os.environ["LFS_SYSROOT"]
env = environment()
env.update(
    {
        "BUILD_CC": "gcc",
        "BUILD_CFLAGS": "",
        "BUILD_CPPFLAGS": "",
        "BUILD_LDFLAGS": "",
    }
)
common = (
    "--prefix=/usr",
    "--with-shared",
    "--without-debug",
    "--without-ada",
    "--without-cxx",
)

for name, extra in (
    ("narrow", ("--with-termlib=tinfo",)),
    ("wide", ("--enable-widec",)),
):
    build = workspace / "build" / ("ncurses-" + name)
    if build.exists():
        shutil.rmtree(build)
    shutil.copytree(source, build)
    subprocess.run(
        [
            str(source / "configure"),
            "--build=x86_64-pc-linux-gnu",
            "--host=i686-lfs-linux-gnu",
            *common,
            "--with-build-cc=gcc",
            "--with-build-cflags=",
            "--with-build-ldflags=",
            "--with-tic-path=/usr/bin/tic",
            *extra,
        ],
        cwd=build,
        env=env,
        check=True,
    )
    subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
    install_env = env.copy()
    install_env["TIC_PATH"] = "/usr/bin/tic"
    subprocess.run(
        ["make", "DESTDIR=" + sysroot, "install"],
        cwd=build,
        env=install_env,
        check=True,
    )
