import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("cups", "cups-2.4.20-source.tar.gz", "cups-2.4.20")
subprocess.run(
    [
        "patch", "-p1", "--forward", "--batch", "-i",
        str(Path(__file__).with_name("local-destination-state.patch").resolve()),
    ],
    cwd=source,
    check=True,
)
configure_make_install(
    source,
    options=(
        "--libdir=/usr/lib",
        "--sysconfdir=/etc",
        "--localstatedir=/var",
        "--with-components=libcups",
        "--enable-shared",
        "--enable-static",
        "--with-tls=openssl",
    ),
)
