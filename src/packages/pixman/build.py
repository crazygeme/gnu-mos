import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("pixman", "pixman-0.46.4.tar.xz", "pixman-0.46.4"),
    "pixman",
    ("-Dtests=disabled",),
)
