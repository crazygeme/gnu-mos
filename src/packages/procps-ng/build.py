import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("procps-ng", "procps-ng-4.0.4.tar.xz", "procps-ng-4.0.4"),
    options=(
        "--disable-kill",
        "--disable-pidof",
        "--disable-systemd",
        "--disable-nls",
    ),
    env_overrides={
        "NCURSES_CFLAGS": "-I" + os.environ["LFS_SYSROOT"] + "/usr/include",
        "NCURSES_LIBS": "-L" + os.environ["LFS_SYSROOT"] + "/usr/lib -lncursesw",
    },
)
