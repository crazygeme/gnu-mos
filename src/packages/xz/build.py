from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("xz", "xz-5.8.1.tar.xz", "xz-5.8.1"),
    options=("--disable-static",),
)
