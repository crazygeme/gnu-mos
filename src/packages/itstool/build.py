import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source("itstool", "itstool-2.0.7.tar.bz2", "itstool-2.0.7")
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env = os.environ.copy()
env.update(
    {
        "PYTHON": str(tools / "bin/python3"),
        "PATH": str(tools / "bin") + ":/usr/bin:/bin",
        "LD_LIBRARY_PATH": str(tools / "lib"),
    }
)
run_configure(
    ["/bin/bash", str(source / "configure"), "--prefix=" + str(tools)],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
