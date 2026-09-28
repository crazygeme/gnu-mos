import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("at-spi2-core", "at-spi2-core-2.56.2.tar.xz", "at-spi2-core-2.56.2"),
    "at-spi2-core",
    options=(
        "-Dintrospection=disabled",
        "-Duse_systemd=false",
    ),
)
