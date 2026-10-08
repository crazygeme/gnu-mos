import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("gdk-pixbuf", "gdk-pixbuf-2.42.12.tar.xz", "gdk-pixbuf-2.42.12"),
    "gdk-pixbuf",
    options=(
        "-Dintrospection=enabled",
        "-Dtests=false",
        "-Dinstalled_tests=false",
        "-Dman=false",
        "-Dbuiltin_loaders=all",
    ),
    introspection=True,
)
