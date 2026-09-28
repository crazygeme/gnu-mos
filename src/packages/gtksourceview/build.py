import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source(
        "gtksourceview", "gtksourceview-4.8.4.tar.xz", "gtksourceview-4.8.4"
    ),
    "gtksourceview",
    options=(
        "-Dgir=false",
        "-Dvapi=false",
        "-Dgtk_doc=false",
        "-Dinstall_tests=false",
    ),
)
