import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("libx11", "libX11-1.8.12.tar.xz", "libX11-1.8.12")
subprocess.run(
    ["patch", "-p1", "-i", str(Path(__file__).with_name("pending-cancellation.patch"))],
    cwd=source,
    check=True,
)
configure_make_install(
    source,
    options=("--disable-static",),
)
