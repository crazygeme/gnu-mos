import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("mousepad", "mousepad-0.6.5.tar.xz", "mousepad-0.6.5"),
    "mousepad",
    options=(
        "-Dgtksourceview4=enabled",
        "-Dkeyfile-settings=true",
        "-Dgspell-plugin=enabled",
        "-Dshortcuts-plugin=enabled",
    ),
)
