import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libcroco", "libcroco-0.6.13.tar.xz", "libcroco-0.6.13"),
    options=(
        "--disable-static",
        "--disable-gtk-doc",
    ),
    env_overrides={"CFLAGS": "-O2 -m32 -std=gnu11"},
)

