import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libnotify", "libnotify-0.8.6.tar.xz", "libnotify-0.8.6"),
    "libnotify",
    options=(
        "-Dintrospection=enabled",
        "-Dtests=false",
        "-Dgtk_doc=false",
        "-Dman=false",
    ),
    introspection=True,
)
