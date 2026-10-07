import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('libpsl', 'libpsl-0.21.5.tar.gz', 'libpsl-0.21.5'),
    options=('--disable-static', '--disable-rpath', '--libdir=/usr/lib', '--enable-runtime=libidn2', '--enable-builtin', '--enable-man'),
)
