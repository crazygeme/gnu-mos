import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("gtkmm", "gtkmm-3.24.10.tar.xz", "gtkmm-3.24.10"),
    "gtkmm",
    options=(
        "-Dmaintainer-mode=false",
        "-Dbuild-documentation=false",
        "-Dbuild-demos=false",
        "-Dbuild-tests=false",
    ),
)

