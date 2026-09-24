import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("markupsafe", "markupsafe-3.0.2.tar.gz", "markupsafe-3.0.2")
site_packages = Path(os.environ["LFS_WORKSPACE"]) / "tools/lib/python3.13/site-packages"
site_packages.mkdir(parents=True, exist_ok=True)
shutil.copytree(source / "src/markupsafe", site_packages / "markupsafe", dirs_exist_ok=True)
