import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("sdl2", "SDL2-2.32.10.tar.gz", "SDL2-2.32.10"),
    options=(
        "--disable-static",
        "--enable-video-x11",
        "--disable-video-wayland",
        "--enable-alsa",
        "--disable-rpath",
    ),
)
