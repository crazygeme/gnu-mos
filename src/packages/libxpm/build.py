import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libxpm", "libXpm-3.5.19.tar.xz", "libXpm-3.5.19"),
    options=("--disable-static",),
    env_overrides={
        "XPM_PATH_GZIP": "/usr/bin/gzip",
        "XPM_PATH_UNCOMPRESS": "/usr/bin/uncompress",
    },
)
