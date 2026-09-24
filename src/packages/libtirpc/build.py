import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source(
    "libtirpc", "libtirpc-1.3.6.tar.bz2", "libtirpc-1.3.6",
    excluded_members=("libtirpc-1.3.6/INSTALL",),
)
patch_file = Path(__file__).with_name("auth-none-prototype.patch")
subprocess.run(
    ["patch", "-p1", "--forward", "--batch", "-i", str(patch_file)],
    cwd=source,
    check=True,
)
configure_make_install(source, options=("--disable-static",))
