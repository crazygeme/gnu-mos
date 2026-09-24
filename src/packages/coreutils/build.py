import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("coreutils", "coreutils-9.7.tar.xz", "coreutils-9.7"),
    options=("--enable-install-program=hostname",),
)
