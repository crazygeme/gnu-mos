import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("xcb-util-wm", "xcb-util-wm-0.4.2.tar.xz", "xcb-util-wm-0.4.2"),
    options=("--disable-static",),
)
