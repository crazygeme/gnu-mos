import os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("python-host", "Python-3.13.7.tar.xz", "Python-3.13.7")
prefix = Path(os.environ["LFS_WORKSPACE"]) / "tools"
build = Path(os.environ["LFS_WORKSPACE"]) / "build/python-host"
build.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update({"CC": "gcc", "CFLAGS": "-std=gnu17", "LDFLAGS": ""})
subprocess.run(
    [str(source / "configure"), "--prefix=" + str(prefix), "--without-ensurepip"],
    cwd=build,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=build, env=env, check=True)
subprocess.run(["make", "install"], cwd=build, env=env, check=True)
