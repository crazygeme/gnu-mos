import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("polkit", "polkit-126.tar.gz", "polkit-126"),
    "polkit",
    options=(
        "--sysconfdir=/etc",
        "--localstatedir=/var",
        "--libdir=lib",
        "-Dsession_tracking=ConsoleKit",
        "-Dpolkitd_user=polkitd",
        "-Dpolkitd_uid=102",
        "-Dprivileged_group=sudo",
        "-Dauthfw=pam",
        "-Dpam_prefix=/etc/pam.d",
        "-Dos_type=lfs",
        "-Dintrospection=false",
        "-Dtests=false",
    ),
)
