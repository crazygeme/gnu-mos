import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libxcrypt", "libxcrypt-4.4.38.tar.xz", "libxcrypt-4.4.38"),
    options=("--disable-static", "--enable-obsolete-api=glibc"),
)
