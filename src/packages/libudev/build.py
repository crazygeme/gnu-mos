import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libudev", "eudev-3.2.14.tar.gz", "eudev-3.2.14"),
    options=("--disable-static", "--disable-manpages"),
)
