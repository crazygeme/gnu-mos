import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source(
        "xf86-video-vesa", "xf86-video-vesa-2.6.0.tar.xz", "xf86-video-vesa-2.6.0"
    ),
    options=("--disable-static", "--with-xorg-module-dir=/usr/lib/xorg/modules"),
)
