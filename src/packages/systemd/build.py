"""Build the system and service manager."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("systemd", "systemd-252.39.tar.gz", "systemd-stable-252.39"),
    "systemd",
    (
        "-Dmode=release",
        "-Dtests=false",
        "-Dinstall-tests=false",
        "-Dman=false",
        "-Dhtml=false",
        "-Defi=false",
        "-Ddefault-hierarchy=legacy",
        "-Dpam=true",
        "-Drootprefix=/usr",
        "-Ddbuspolicydir=/usr/share/dbus-1/system.d",
        "-Ddbussessionservicedir=/usr/share/dbus-1/services",
        "-Ddbussystemservicedir=/usr/share/dbus-1/system-services",
        "-Ddbus-interfaces-dir=/usr/share/dbus-1/interfaces",
        "-Dsysvinit-path=",
        "-Dsysvrcnd-path=",
    ),
    host_tools=(),
)
