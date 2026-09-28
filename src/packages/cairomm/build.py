import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("cairomm", "cairomm-1.14.5.tar.xz", "cairomm-1.14.5"),
    "cairomm",
    options=(
        "-Dmaintainer-mode=false",
        "-Dbuild-documentation=false",
        "-Dbuild-examples=false",
        "-Dbuild-tests=false",
    ),
)
