import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install
meson_install(archive_source("xorg-server", "xorg-server-21.1.18.tar.xz", "xorg-server-21.1.18"), "xorg-server", ("-Dxorg=true", "-Dxwayland=true", "-Dxephyr=true", "-Dxnest=true", "-Dxvfb=true", "-Ddocs=false"))
