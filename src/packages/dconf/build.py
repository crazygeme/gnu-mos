import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("dconf", "dconf-0.40.0.tar.xz", "dconf-0.40.0"),
    "dconf",
    options=(
        "--sysconfdir=/etc",
        "--libexecdir=/usr/libexec",
        "-Dman=false",
        "-Dgtk_doc=false",
    ),
    env_overrides={"PKG_CONFIG_FDO_SYSROOT_RULES": "1"},
)
