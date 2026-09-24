import os, subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("linux-api-headers", "linux-6.16.8.tar.xz", "linux-6.16.8")
subprocess.run(["make", "mrproper"], cwd=source, check=True)
subprocess.run(
    [
        "make",
        "ARCH=x86",
        "headers_install",
        "INSTALL_HDR_PATH=" + str(Path(os.environ["LFS_SYSROOT"]) / "usr"),
    ],
    cwd=source,
    check=True,
)
