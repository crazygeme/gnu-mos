import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

workspace = Path(os.environ["LFS_WORKSPACE"])
sysroot = Path(os.environ["LFS_SYSROOT"])
meson_install(
    archive_source("gobject-introspection", "gobject-introspection-1.84.0.tar.xz", "gobject-introspection-1.84.0"),
    "gobject-introspection",
    options=(
        "--wrap-mode=nofallback",
        "-Dpython=" + str(workspace / "tools/bin/python3.13"),
        "-Dpython.purelibdir=/usr/lib/python3.13/site-packages",
        "-Dpython.platlibdir=/usr/lib/python3.13/site-packages",
        "-Dgi_cross_use_prebuilt_gi=true",
        "-Dgi_cross_binary_wrapper=" + str(workspace / "tools/bin/lfs-run-target"),
        "-Dgi_cross_ldd_wrapper=" + str(workspace / "tools/bin/lfs-ldd-target"),
        "-Dgi_cross_pkgconfig_sysroot_path=",
        "-Dtests=false",
    ),
    introspection=True,
    python_cross=True,
)
for name in ("g-ir-scanner", "g-ir-annotation-tool"):
    script = sysroot / "usr/bin" / name
    contents = script.read_text().split("\n", 1)[1]
    script.write_text("#!/usr/bin/python3\n" + contents)
