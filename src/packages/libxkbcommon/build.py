import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source(
        "libxkbcommon",
        "libxkbcommon-1.8.1.tar.gz",
        "libxkbcommon-xkbcommon-1.8.1",
    ),
    "libxkbcommon",
    ("--libdir=lib", "-Denable-wayland=false"),
)
