import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libepoxy", "libepoxy-1.5.10.tar.xz", "libepoxy-1.5.10"),
    "libepoxy",
    options=("-Dtests=false",),
)
