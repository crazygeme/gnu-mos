import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("pcre2", "pcre2-10.46.tar.bz2", "pcre2-10.46"),
    options=(
        "--libdir=/usr/lib",
        "--enable-shared",
        "--disable-static",
        "--enable-unicode",
    ),
)
