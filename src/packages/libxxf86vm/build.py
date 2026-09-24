import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libxxf86vm", "libXxf86vm-1.1.6.tar.xz", "libXxf86vm-1.1.6"),
    options=("--disable-static",),
)
