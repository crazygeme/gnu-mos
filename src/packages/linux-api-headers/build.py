import os, subprocess
from pathlib import Path
source = Path(os.environ["LFS_SOURCES"]) / "linux-6.16.8"
subprocess.run(["make", "mrproper"], cwd=source, check=True)
subprocess.run(["make", "ARCH=x86", "headers_install", "INSTALL_HDR_PATH=" + str(Path(os.environ["LFS_SYSROOT"]) / "usr")], cwd=source, check=True)
