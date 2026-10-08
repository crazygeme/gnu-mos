import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('bison-target', 'bison-3.8.2.tar.xz', 'bison-3.8.2'),
    env_overrides={
        'CFLAGS': "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -std=gnu17",
        'M4': '/usr/bin/m4',
    },
)
