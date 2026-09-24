import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("xorgproto", "xorgproto-2024.1.tar.xz", "xorgproto-2024.1"),
    "xorgproto",
)
