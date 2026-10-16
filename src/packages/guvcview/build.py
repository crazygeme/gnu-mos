import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install
cmake_install('guvcview', 'guvcview-src-2.2.2.tar.bz2', 'guvcview-2.2.2', options=("-DUSE_GTK3=ON", "-DUSE_SDL2=ON", "-DINSTALL_DEVKIT=ON", "-DCMAKE_INSTALL_DATADIR=/usr/share"))
