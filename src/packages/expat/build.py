import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("expat", "expat-2.7.1.tar.xz", "expat-2.7.1"),
    options=("--disable-static", "--without-xmlwf", "--without-docbook"),
)
