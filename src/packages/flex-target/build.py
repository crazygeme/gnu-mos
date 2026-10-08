import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('flex-target', 'flex-2.6.4.tar.gz', 'flex-2.6.4'),
    env_overrides={
        'CFLAGS': "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -std=gnu17",
        'CC_FOR_BUILD': 'gcc',
        'CFLAGS_FOR_BUILD': '-O2 -std=gnu17',
        'M4': '/usr/bin/m4',
        'ac_cv_func_malloc_0_nonnull': 'yes',
        'ac_cv_func_realloc_0_nonnull': 'yes',
    },
)
