import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("util-linux", "util-linux-2.41.1.tar.xz", "util-linux-2.41.1"),
    options=(
        "--disable-bash-completion",
        "--disable-systemd",
        "--disable-libuuid",
        "--disable-makeinstall-tty-setgid",
        "--disable-makeinstall-setuid",
        "--disable-makeinstall-chown",
    ),
)
