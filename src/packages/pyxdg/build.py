import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("pyxdg", "pyxdg-0.28.tar.gz", "pyxdg-0.28")
destination = Path(os.environ["LFS_SYSROOT"]) / "usr/lib/python3.13/site-packages/xdg"
shutil.copytree(source / "xdg", destination, dirs_exist_ok=True)
