import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("atkmm", "atkmm-2.28.4.tar.xz", "atkmm-2.28.4"),
    "atkmm",
    options=(
        "-Dmaintainer-mode=false",
        "-Dbuild-documentation=false",
    ),
)

