import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source("polkit", "polkit-126.tar.gz", "polkit-126")
subprocess.run(
    ["patch", "--batch", "--forward", "-p1", "-i",
     str(Path(__file__).with_name("systemd-service-type.patch").resolve())],
    cwd=source, check=True,
)
meson_install(
    source,
    "polkit",
    options=(
        "--sysconfdir=/etc",
        "--localstatedir=/var",
        "--libdir=lib",
        "-Dsession_tracking=logind",
        "-Dsystemdsystemunitdir=/usr/lib/systemd/system",
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
