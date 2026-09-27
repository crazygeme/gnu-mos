import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("gspell", "gspell-1.12.2.tar.xz", "gspell-1.12.2"),
    options=(
        "--disable-static",
        "--disable-introspection",
        "--disable-vala",
        "--disable-gtk-doc",
    ),
    host_tools=("glib-compile-resources", "glib-mkenums", "glib-compile-schemas"),
)

