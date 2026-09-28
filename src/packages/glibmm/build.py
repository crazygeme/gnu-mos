import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("glibmm", "glibmm-2.66.8.tar.xz", "glibmm-2.66.8"),
    "glibmm",
    options=(
        "-Dmaintainer-mode=false",
        "-Dbuild-documentation=false",
        "-Dbuild-examples=false",
    ),
)
