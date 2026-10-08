import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('autoconf', 'autoconf-2.72.tar.xz', 'autoconf-2.72'),
    env_overrides={
        'PERL': '/usr/bin/perl',
        'M4': '/usr/bin/m4',
    },
)
