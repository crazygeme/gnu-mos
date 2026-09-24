import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("ninja", "ninja-1.13.1.tar.gz", "ninja-1.13.1")
subprocess.run(
    [str(Path(os.environ["LFS_WORKSPACE"]) / "tools/bin/python3.13"), "configure.py", "--bootstrap"],
    cwd=source,
    check=True,
)
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools/bin"
tools.mkdir(parents=True, exist_ok=True)
shutil.copy2(source / "ninja", tools / "ninja")
(tools / "ninja").chmod(0o755)
