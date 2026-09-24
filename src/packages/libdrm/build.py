import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libdrm", "libdrm-2.4.124.tar.xz", "libdrm-2.4.124"),
    "libdrm",
)
