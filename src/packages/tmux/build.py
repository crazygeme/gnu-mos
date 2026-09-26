import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("tmux", "tmux-3.5a.tar.gz", "tmux-3.5a"),
    options=("--disable-utf8proc",),
    env_overrides={
        "LIBTINFO_CFLAGS": "-I" + os.environ["LFS_SYSROOT"] + "/usr/include",
        "LIBTINFO_LIBS": "-L"
        + os.environ["LFS_SYSROOT"]
        + "/usr/lib -ltinfo -lncursesw",
    },
)
