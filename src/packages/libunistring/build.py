import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('libunistring', 'libunistring-1.4.tar.xz', 'libunistring-1.4'),
    options=('--disable-static', '--libdir=/usr/lib'),
)
