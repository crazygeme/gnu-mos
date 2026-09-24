import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libxrandr", "libXrandr-1.5.4.tar.xz", "libXrandr-1.5.4"),
    options=("--disable-static", "--enable-malloc0returnsnull"),
)
