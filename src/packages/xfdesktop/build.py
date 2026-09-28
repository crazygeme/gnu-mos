import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("xfdesktop", "xfdesktop-4.20.0.tar.bz2", "xfdesktop-4.20.0")
subprocess.run(
    [
        "patch",
        "-p1",
        "--forward",
        "--batch",
        "-i",
        str(Path(__file__).with_name("backdrop-loader-lifetime.patch").resolve()),
    ],
    cwd=source,
    check=True,
)

configure_make_install(
    source,
    host_tools=(
        "gdbus-codegen",
        "glib-compile-resources",
        "glib-genmarshal",
        "glib-mkenums",
    ),
    options=(
        "--sysconfdir=/etc",
        "--disable-static",
        "--enable-x11",
        "--disable-wayland",
        "--with-default-backdrop-filename=/usr/share/backgrounds/xfce/xfce-blue.jpg",
    ),
)
