import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libpng", "libpng-1.6.44.tar.xz", "libpng-1.6.44"),
    options=("--disable-static",),
)
