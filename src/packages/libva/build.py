import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libva", "libva-2.22.0.tar.bz2", "libva-2.22.0"),
    "libva",
    options=(
        "--libdir=lib",
        "-Ddriverdir=/usr/lib/dri",
        "-Dwith_x11=yes",
        "-Dwith_glx=no",
        "-Dwith_wayland=no",
        "-Dwith_win32=no",
    ),
    host_tools=(),
)
