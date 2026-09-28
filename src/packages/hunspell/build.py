import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("hunspell", "hunspell-1.7.2.tar.gz", "hunspell-1.7.2"),
    options=("--disable-static",),
)
