import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('libtool', 'libtool-2.5.4.tar.xz', 'libtool-2.5.4'),
    env_overrides={
        'SED': '/usr/bin/sed',
        'GREP': '/usr/bin/grep',
        'EGREP': '/usr/bin/grep -E',
        'FGREP': '/usr/bin/grep -F',
    },
)
