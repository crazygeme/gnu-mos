import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("pyzy", "libpyzy-1.0.1.tar.xz", "libpyzy-1.0.1")
subprocess.run(
    ["patch", "-p1", "--batch", "--forward", "-i",
     str(Path(__file__).with_name("python3-dictionary.patch"))],
    cwd=source, check=True,
)
subprocess.run(["autoreconf", "-fi"], cwd=source, check=True)
configure_make_install(
    source,
    options=("--enable-db-android",),
    env_overrides={
        "CXXFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -std=gnu++11",
        "PYTHON": "/usr/bin/python3",
        "SQLITE3": "/usr/bin/sqlite3",
        "am_cv_pathless_PYTHON": "python3",
        "am_cv_python_version": "3.13",
        "am_cv_python_pythondir": "/usr/lib/python3.13/site-packages",
        "am_cv_python_pyexecdir": "/usr/lib/python3.13/site-packages",
    },
)
