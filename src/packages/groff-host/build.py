import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("groff-host", "groff-1.23.0.tar.gz", "groff-1.23.0")
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env = os.environ.copy()
subprocess.run(
    [
        str(source / "configure"),
        "--prefix=" + str(tools),
        "--without-x",
        "--with-uchardet=no",
    ],
    cwd=source,
    env=env,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, env=env, check=True)
subprocess.run(["make", "install"], cwd=source, env=env, check=True)
