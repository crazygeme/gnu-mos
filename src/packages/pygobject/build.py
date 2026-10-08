import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("pygobject", "pygobject-3.50.0.tar.xz", "pygobject-3.50.0"),
    "pygobject",
    options=(
        "-Dtests=false",
        "-Dpycairo=enabled",
        "-Dpython=" + str(Path(os.environ["LFS_WORKSPACE"]) / "tools/bin/python3.13"),
        "-Dpython.purelibdir=/usr/lib/python3.13/site-packages",
        "-Dpython.platlibdir=/usr/lib/python3.13/site-packages",
    ),
    python_cross=True,
)
