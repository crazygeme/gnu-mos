import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("pyyaml", "pyyaml-6.0.2.tar.gz", "pyyaml-6.0.2")
site_packages = Path(os.environ["LFS_WORKSPACE"]) / "tools/lib/python3.13/site-packages"
site_packages.mkdir(parents=True, exist_ok=True)
shutil.copytree(source / "lib/yaml", site_packages / "yaml", dirs_exist_ok=True)
shutil.copytree(source / "lib/_yaml", site_packages / "_yaml", dirs_exist_ok=True)
