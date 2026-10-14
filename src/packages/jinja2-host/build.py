import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source('jinja2-host', 'jinja2-3.1.6.tar.gz', 'jinja2-3.1.6')
site_packages = Path(os.environ["LFS_WORKSPACE"]) / "tools/lib/python3.13/site-packages"
site_packages.mkdir(parents=True, exist_ok=True)
shutil.copytree(source / 'src/jinja2', site_packages / 'jinja2', dirs_exist_ok=True)
