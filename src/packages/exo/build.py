import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("exo", "exo-4.20.0.tar.bz2", "exo-4.20.0"),
    options=(
        "--sysconfdir=/etc",
        "--disable-static",
    ),
)
