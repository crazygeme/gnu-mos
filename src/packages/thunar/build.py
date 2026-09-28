import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("thunar", "thunar-4.20.0.tar.bz2", "thunar-4.20.0"),
    host_tools=("glib-compile-resources",),
    options=(
        "--disable-introspection",
        "--sysconfdir=/etc",
        "--disable-static",
    ),
)
