import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("glib-introspection", "glib-2.88.1.tar.xz", "glib-2.88.1"),
    "glib-introspection",
    options=(
        "--wrap-mode=nofallback",
        "-Dintrospection=enabled",
        "-Dtests=false",
    ),
    introspection=True,
)
