import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("xdm", "xdm-1.1.17.tar.xz", "xdm-1.1.17"),
    options=(
        "--sysconfdir=/etc",
        "--localstatedir=/var",
        "--with-xdmconfigdir=/etc/X11/xdm",
        "--with-xdmscriptdir=/etc/X11/xdm",
        "--with-authdir=/run/xdm",
        "--with-piddir=/run",
        "--with-logdir=/var/log",
        "--with-default-vt=vt2",
        "--with-default-session=/usr/bin/mos-xfce-session",
        "--with-xrdb=/usr/bin/xrdb",
        "--with-random-device=/dev/urandom",
        "--with-pam",
        "--with-xft",
        "--without-systemd-daemon",
        "--without-systemdsystemunitdir",
    ),
)
