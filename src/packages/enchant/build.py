import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("enchant", "enchant-2.8.2.tar.gz", "enchant-2.8.2"),
    options=(
        "--disable-static",
        "--with-hunspell",
        "--without-aspell",
        "--without-hspell",
        "--without-nuspell",
        "--without-voikko",
    ),
)

