import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libice", "libICE-1.1.2.tar.xz", "libICE-1.1.2"),
    options=("--disable-static",),
)
