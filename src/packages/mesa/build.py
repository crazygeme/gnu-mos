import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source("mesa", "mesa-25.1.9.tar.xz", "mesa-25.1.9"),
    "mesa",
    (
        "-Dplatforms=x11",
        "-Dgallium-drivers=softpipe",
        "-Dvulkan-drivers=",
        "-Dglx=dri",
        "-Degl=enabled",
        "-Dgbm=enabled",
        "-Dllvm=disabled",
    ),
)

pkgconfig = Path(os.environ["LFS_SYSROOT"]) / "usr/lib/pkgconfig"
pkgconfig.mkdir(parents=True, exist_ok=True)
(pkgconfig / "dri.pc").write_text(
    "prefix=/usr\n"
    "libdir=${prefix}/lib\n"
    "dridriverdir=${libdir}/dri\n"
    "Name: dri\n"
    "Description: Mesa DRI driver directory\n"
    "Version: 25.1.9\n",
    encoding="ascii",
)
