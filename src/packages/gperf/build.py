import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source("gperf", "gperf-3.3.tar.gz", "gperf-3.3")
prefix = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env = os.environ.copy()
env.update(
    {"CC": "gcc", "CXX": "g++", "CFLAGS": "-O2", "CXXFLAGS": "-O2", "LDFLAGS": ""}
)
run_configure(
    [str(source / "configure"), "--prefix=" + str(prefix)],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
