import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install
meson_install(archive_source("gtk", "gtk-4.20.1.tar.xz", "gtk-4.20.1"), "gtk", ("-Dbuild-tests=false", "-Dbuild-examples=false", "-Dwayland-backend=false"))
