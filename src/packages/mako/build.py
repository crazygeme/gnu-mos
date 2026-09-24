import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("mako", "mako-1.3.10.tar.gz", "mako-1.3.10")
site_packages = Path(os.environ["LFS_WORKSPACE"]) / "tools/lib/python3.13/site-packages"
site_packages.mkdir(parents=True, exist_ok=True)
shutil.copytree(source / "mako", site_packages / "mako", dirs_exist_ok=True)
