import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install
meson_install(archive_source("gnome-shell", "gnome-shell-48.4.tar.xz", "gnome-shell-48.4"), "gnome-shell", ("-Dtests=false",))
