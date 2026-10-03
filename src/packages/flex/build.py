import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import run_configure, archive_source

source = archive_source("flex", "flex-2.6.4.tar.gz", "flex-2.6.4")
prefix = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env = os.environ.copy()
env.update({"CC": "gcc", "CFLAGS": "-O2", "LDFLAGS": ""})
run_configure(
    [str(source / "configure"), "--prefix=" + str(prefix), "--disable-shared"],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
