import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("alsa-lib", "alsa-lib-1.2.14.tar.bz2", "alsa-lib-1.2.14"),
    options=("--disable-static", "--sysconfdir=/etc"),
)
