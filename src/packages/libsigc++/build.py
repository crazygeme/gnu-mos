import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libsigc++", "libsigc++-2.12.1.tar.xz", "libsigc++-2.12.1"),
    "libsigc++",
    options=(
        "-Dmaintainer-mode=false",
        "-Dbuild-documentation=false",
        "-Dbuild-examples=false",
        "-Dbuild-tests=false",
        "-Dvalidation=false",
    ),
)

