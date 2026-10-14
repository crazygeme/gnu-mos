import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source('glad-host', 'glad2-2.0.8.tar.gz', 'glad2-2.0.8')
site_packages = Path(os.environ["LFS_WORKSPACE"]) / "tools/lib/python3.13/site-packages"
site_packages.mkdir(parents=True, exist_ok=True)
shutil.copytree(source / 'glad', site_packages / 'glad', dirs_exist_ok=True)
