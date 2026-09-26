import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('fontconfig', 'fontconfig-2.16.0.tar.xz', 'fontconfig-2.16.0'),
    options=(
        '--disable-static',
        '--sysconfdir=/etc',
        '--localstatedir=/var',
    ),
)
