import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("harfbuzz", "harfbuzz-11.2.1.tar.xz", "harfbuzz-11.2.1"),
    "harfbuzz",
    ("-Dtests=disabled", "-Ddocs=disabled", "-Dintrospection=disabled"),
)
