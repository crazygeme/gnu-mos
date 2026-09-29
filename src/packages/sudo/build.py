import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("sudo", "sudo-1.9.17p2.tar.gz", "sudo-1.9.17p2"),
    # Root ownership is assigned during setup and boot initialization.
    install_options=("INSTALL_OWNER=",),
    options=(
        "--sysconfdir=/etc",
        "--libexecdir=/usr/lib",
        "--localstatedir=/var",
        "--with-rundir=/run/sudo",
        "--with-vardir=/var/lib/sudo",
        "--with-pam",
        "--with-pam-login",
        "--with-logging=syslog",
        "--with-logfac=auth",
        "--with-env-editor",
        "--with-editor=/usr/bin/vim",
    ),
)
