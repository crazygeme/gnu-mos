import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source("python", "Python-3.13.7.tar.xz", "Python-3.13.7")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/python"
build.mkdir(parents=True, exist_ok=True)
sysroot = os.environ["LFS_SYSROOT"]
env = os.environ.copy()
config_site = build / "config.site"
config_site.write_text(
    "ac_cv_file__dev_ptmx=yes\n" "ac_cv_file__dev_ptc=no\n",
    encoding="ascii",
)
env.update(
    {
        "CC": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-gcc",
        "CXX": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-g++",
        "AR": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ar",
        "RANLIB": os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu") + "-ranlib",
        "CFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32"),
        "LDFLAGS": "--sysroot=" + sysroot,
        "CONFIG_SITE": str(config_site),
    }
)
run_configure(
    [
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu"),
        "--prefix=/usr",
        "--with-build-python="
        + str(Path(os.environ["LFS_WORKSPACE"]) / "tools/bin/python3.13"),
        "--enable-ipv6",
        "--without-ensurepip",
        "--disable-test-modules",
    ],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + sysroot, "install"], cwd=build, env=env, check=True
)
