import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("pangomm", "pangomm-2.46.4.tar.xz", "pangomm-2.46.4"),
    "pangomm",
    options=(
        "-Dmaintainer-mode=false",
        "-Dbuild-documentation=false",
    ),
)

