import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("gnome-session", "gnome-session-48.0.tar.xz", "gnome-session-48.0"),
    "gnome-session",
)
