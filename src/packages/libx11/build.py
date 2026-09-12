import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install
configure_make_install(archive_source("libx11", "libX11-1.8.12.tar.xz", "libX11-1.8.12"), options=("--disable-static",))
