import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
sysroot = Path(os.environ["LFS_SYSROOT"])
configure_make_install(
    archive_source("ibus", "ibus-1.5.32.tar.gz", "ibus-1.5.32"),
    options=(
        "--sysconfdir=/etc", "--libexecdir=/usr/libexec",
        "--disable-systemd-services", "--disable-python2",
        "--disable-gtk2", "--disable-gtk4", "--disable-wayland",
        "--disable-appindicator", "--disable-emoji-dict", "--disable-unicode-dict",
        "--enable-gtk3", "--enable-xim", "--enable-dconf", "--enable-ui", "--enable-setup",
        "--enable-introspection", "--disable-tests",
        "--with-python-overrides-dir=/usr/lib/python3.13/site-packages/gi/overrides",
    ),
    env_overrides={
        "CC_FOR_BUILD": "gcc",
        "CFLAGS_FOR_BUILD": "-O2 -std=gnu17",
        "CPPFLAGS_FOR_BUILD": "",
        "LDFLAGS_FOR_BUILD": "",
        "PKG_CONFIG_FDO_SYSROOT_RULES": "1",
        "PKG_CONFIG_FOR_BUILD": (
            "/usr/bin/env -u PKG_CONFIG_SYSROOT_DIR -u PKG_CONFIG_LIBDIR "
            "-u PKG_CONFIG_PATH /usr/bin/pkg-config"
        ),
        "PYTHON": "/usr/bin/python3",
        "am_cv_python_version": "3.13",
        "am_cv_python_pythondir": "/usr/lib/python3.13/site-packages",
        "am_cv_python_pyexecdir": "/usr/lib/python3.13/site-packages",
        "VALAC": "/usr/bin/valac",
        "GI_TYPELIB_PATH": str(sysroot / "usr/lib/girepository-1.0"),
    },
    make_options=(
        "IBusIMModule_1_0_gir_SCANNERFLAGS="
        "--header-only --pkg=glib-2.0 --warn-all "
        "--identifier-prefix=IBus --symbol-prefix=ibus --c-include=ibus.h",
        "IBus_1_0_gir_LIBS=ibus-1.0",
        "IBus_1_0_gir_LDFLAGS=-L" + str(tools.parent / "build/ibus-1.5.32/src/.libs"),
        "VAPIGEN=/usr/bin/vapigen",
        "VAPIGEN_GIRDIRS=" + str(sysroot / "usr/share/gir-1.0"),
        "INTROSPECTION_SCANNER=" + str(tools / "bin/g-ir-scanner-cross"),
        "INTROSPECTION_COMPILER=" + str(tools / "bin/g-ir-compiler-cross"),
        "INTROSPECTION_MAKEFILE=" + str(tools / "share/gobject-introspection-1.0/Makefile.introspection"),
    ),
    build_options=("MAKE=make -W application.vala -W main.vala",),
)
