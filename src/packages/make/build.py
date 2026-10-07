import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("make", "make-4.4.1.tar.gz", "make-4.4.1"),
)
