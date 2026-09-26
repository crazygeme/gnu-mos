import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("nasm-host", "nasm-2.16.03.tar.xz", "nasm-2.16.03")
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
subprocess.run(
    [str(source / "configure"), "--prefix=" + str(tools)],
    cwd=source,
    check=True,
)
subprocess.run(["make", "-j4"], cwd=source, check=True)
subprocess.run(["make", "install"], cwd=source, check=True)
