import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("dbus", "dbus-1.16.2.tar.xz", "dbus-1.16.2"),
    "dbus",
    (
        "-Dsystemd=enabled",
        "-Dsystemd_system_unitdir=/usr/lib/systemd/system",
        "-Dsystemd_user_unitdir=/usr/lib/systemd/user",
        "-Dintrusive_tests=false",
        "-Dmodular_tests=disabled",
        "-Dinstalled_tests=false",
    ),
)
