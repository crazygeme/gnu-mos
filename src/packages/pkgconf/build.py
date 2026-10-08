import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('pkgconf', 'pkgconf-2.5.1.tar.xz', 'pkgconf-2.5.1'),
    options=(
        '--with-pkg-config-dir=/usr/local/lib/pkgconfig:/usr/local/share/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig',
        '--with-system-libdir=/lib:/usr/lib',
        '--with-system-includedir=/usr/include',
    ),
)
