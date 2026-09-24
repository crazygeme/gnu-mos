import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libxi", "libXi-1.8.2.tar.xz", "libXi-1.8.2"),
    options=("--disable-static", "--enable-malloc0returnsnull"),
)
