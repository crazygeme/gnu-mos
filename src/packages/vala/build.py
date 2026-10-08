import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("vala", "vala-0.56.18.tar.xz", "vala-0.56.18"),
    options=("--disable-valadoc",),
    env_overrides={
        "CFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -std=gnu17",
        "VALAC": "/usr/bin/valac",
        "PKG_CONFIG_FDO_SYSROOT_RULES": "1",
    },
)
