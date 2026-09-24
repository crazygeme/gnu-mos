import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("xcb-proto", "xcb-proto-1.17.0.tar.xz", "xcb-proto-1.17.0"),
    options=("--disable-silent-rules",),
)
