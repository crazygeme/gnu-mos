from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source("iputils", "iputils-20250605.tar.gz", "iputils-20250605")
meson_install(
    source,
    "iputils",
    (
        "-DBUILD_TRACEPATH=true",
        "-DBUILD_PING=true",
        "-DBUILD_ARPING=false",
        "-DBUILD_MANS=true",
    ),
)
