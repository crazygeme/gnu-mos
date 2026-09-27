import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("xf86-input-keyboard", "xf86-input-keyboard-1.9.0.tar.bz2", "xf86-input-keyboard-1.9.0"),
    options=("--disable-static", "--with-xorg-module-dir=/usr/lib/xorg/modules"),
)
