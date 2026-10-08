import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("python-setuptools", "setuptools-80.9.0.tar.gz", "setuptools-80.9.0")
for prefix in (Path(os.environ["LFS_WORKSPACE"]) / "tools", Path(os.environ["LFS_SYSROOT"]) / "usr"):
    destination = prefix / "lib/python3.13/site-packages"
    destination.mkdir(parents=True, exist_ok=True)
    for module in ("setuptools", "_distutils_hack", "pkg_resources"):
        shutil.copytree(source / module, destination / module, dirs_exist_ok=True)
    shutil.copytree(
        source / "setuptools.egg-info", destination / "setuptools-80.9.0.egg-info",
        dirs_exist_ok=True,
    )
    (destination / "distutils-precedence.pth").write_text(
        "import os; enabled = os.environ.get('SETUPTOOLS_USE_DISTUTILS', 'local') == 'local'; "
        "enabled and __import__('_distutils_hack').add_shim()\n"
    )
