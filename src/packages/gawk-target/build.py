import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('gawk-target', 'gawk-5.3.2.tar.xz', 'gawk-5.3.2'),
    env_overrides={
        'CFLAGS': "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -std=gnu17",
    },
)
