import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("sysklogd", "sysklogd-2.7.2.tar.gz", "sysklogd-2.7.2"),
    options=(
        "--sysconfdir=/etc",
        "--localstatedir=/var",
        "--runstatedir=/run",
        "--without-systemd",
        # The util-linux package provides /usr/bin/logger.
        "--without-logger",
    ),
)
