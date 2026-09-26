import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("libpciaccess", "libpciaccess-0.18.1.tar.xz", "libpciaccess-0.18.1"),
    "libpciaccess",
    options=("-Dzlib=enabled",),
    host_tools=(),
)
