import os, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

src = archive_source("grub", "grub-2.14.tar.xz", "grub-2.14")
b = Path(os.environ["LFS_WORKSPACE"]) / "build/grub-build"
if b.exists():
    shutil.rmtree(b)
b.mkdir(parents=True)
env = os.environ.copy()
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env["PATH"] = str(tools / "bin") + ":/usr/bin:/bin:" + env.get("PATH", "")
env["ax_cv_check_ldflags___Wl___image_base_0x400000"] = "no"
run_configure(
    [
        str(src / "configure"),
        "--prefix=/usr",
        "--target=i386",
        "--with-platform=pc",
        "--disable-werror",
    ],
    cwd=b,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=b, env=env, check=True)
subprocess.run(
    ["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"],
    cwd=b,
    env=env,
    check=True,
)
