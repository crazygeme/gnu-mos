import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('libidn2', 'libidn2-2.3.8.tar.gz', 'libidn2-2.3.8'),
    options=('--disable-static', '--disable-rpath', '--libdir=/usr/lib'),
)
