import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

workspace = Path(os.environ["LFS_WORKSPACE"])
tools = workspace / "tools"
sysroot = Path(os.environ["LFS_SYSROOT"])
build_libdir = workspace / "build/xfce4-panel-4.20.0/libxfce4panel/.libs"

configure_make_install(
    archive_source("xfce4-panel", "xfce4-panel-4.20.0.tar.bz2", "xfce4-panel-4.20.0"),
    host_tools=("gdbus-codegen",),
    options=(
        "--sysconfdir=/etc",
        "--disable-static",
        "--enable-x11",
        "--disable-wayland",
        "--enable-introspection",
    ),
    env_overrides={
        "PKG_CONFIG_FDO_SYSROOT_RULES": "1",
        "GI_TYPELIB_PATH": str(sysroot / "usr/lib/girepository-1.0"),
    },
    make_options=(
        "INTROSPECTION_SCANNER=" + str(tools / "bin/g-ir-scanner-cross"),
        "INTROSPECTION_COMPILER=" + str(tools / "bin/g-ir-compiler-cross"),
        "INTROSPECTION_MAKEFILE=" + str(tools / "share/gobject-introspection-1.0/Makefile.introspection"),
        "Libxfce4panel_2_0_gir_LIBS=xfce4panel-2.0",
        "Libxfce4panel_2_0_gir_LDFLAGS=-L" + str(build_libdir),
        "VAPIGEN=/usr/bin/vapigen",
        "VAPIGEN_MAKEFILE=/usr/share/vala/Makefile.vapigen",
        "VAPIGEN_VAPIDIRS=" + str(sysroot / "usr/share/vala/vapi"),
        "VAPIGEN_GIRDIRS=" + str(sysroot / "usr/share/gir-1.0"),
    ),
)
