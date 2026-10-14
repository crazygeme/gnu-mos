import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source("mesa", "mesa-25.1.9.tar.xz", "mesa-25.1.9")
meson_install(
    source,
    "mesa",
    (
        "--libdir=lib",
        "-Dplatforms=x11",
        "-Dgallium-drivers=virgl",
        "-Dgallium-va=enabled",
        "-Dvideo-codecs=all",
        "-Dvulkan-drivers=virtio",
        "-Dglx=dri",
        "-Degl=enabled",
        "-Dgbm=enabled",
        "-Dllvm=disabled",
        "--buildtype=release",
        "-Dgles1=enabled",
        "-Dgles2=enabled",
    ),
    env_overrides={
        # Vulkan pNext chains share headers across distinct structure types.
        "CFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -fno-strict-aliasing -g",
        "CXXFLAGS": "-O2 -m" + os.environ.get("LFS_BITS", "32") + " -fno-strict-aliasing -g",
    },
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
