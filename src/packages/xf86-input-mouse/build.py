import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source(
        "xf86-input-mouse", "xf86-input-mouse-1.9.5.tar.xz", "xf86-input-mouse-1.9.5"
    ),
    options=("--disable-static", "--with-xorg-module-dir=/usr/lib/xorg/modules"),
)
