import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install
meson_install(archive_source('libv4l', 'v4l-utils-1.30.1.tar.xz', 'v4l-utils-1.30.1'), 'libv4l', options=("-Djpeg=enabled", "-Dv4l-utils=false", "-Dlibdvbv5=disabled", "-Ddoxygen-doc=disabled"))
