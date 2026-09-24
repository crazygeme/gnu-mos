import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libxcvt", "libxcvt-0.1.3.tar.xz", "libxcvt-0.1.3"),
    "libxcvt",
)
