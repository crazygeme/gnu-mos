import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("linux-pam", "Linux-PAM-1.7.1.tar.xz", "Linux-PAM-1.7.1"),
    "linux-pam",
    options=("--sysconfdir=/etc", "--libdir=lib", "-Dpam_unix=enabled"),
)
