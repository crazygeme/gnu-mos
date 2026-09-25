import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("util-linux", "util-linux-2.41.1.tar.xz", "util-linux-2.41.1")
patch = Path(__file__).with_name("lastlog2-libm.patch")
subprocess.run(
    ["patch", "-p1", "--forward", "--batch", "-i", str(patch)], cwd=source, check=True
)

configure_make_install(
    source,
    options=(
        "--disable-bash-completion",
        "--disable-systemd",
        "--disable-libuuid",
        "--disable-makeinstall-tty-setgid",
        "--disable-makeinstall-setuid",
        "--disable-makeinstall-chown",
    ),
)
