import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install
meson_install(archive_source("glib", "glib-2.86.0.tar.xz", "glib-2.86.0"), "glib")
