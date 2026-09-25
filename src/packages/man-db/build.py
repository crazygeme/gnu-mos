from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("man-db", "man-db-2.13.0.tar.xz", "man-db-2.13.0"),
    options=(
        "--disable-setuid",
        "--disable-cache-owner",
        "--with-systemdtmpfilesdir=no",
    ),
)
