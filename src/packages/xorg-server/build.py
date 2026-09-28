import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source(
    "xorg-server", "xorg-server-21.1.18.tar.xz", "xorg-server-21.1.18"
)
for patch_name in ("linux-ioports.patch", "target-dri-path.patch"):
    subprocess.run(
        [
            "patch",
            "-p1",
            "--forward",
            "--batch",
            "-i",
            str(Path(__file__).with_name(patch_name).resolve()),
        ],
        cwd=source,
        check=True,
    )

meson_install(
    source,
    "xorg-server",
    (
        "--cross-file=" + str(Path(__file__).with_name("mos-cross.ini").resolve()),
        "-Dxorg=true",
        "-Dglamor=true",
        "-Ddri2=true",
        "-Ddri3=true",
        "-Dglx=true",
        "-Dxephyr=true",
        "-Dxnest=true",
        "-Dxvfb=true",
        "-Ddocs=false",
        "-Dsuid_wrapper=true",
        "-Ddefault_font_path=built-ins",
        "-Dxkb_dir=/usr/share/X11/xkb",
        "-Dxkb_output_dir=/var/lib/xkb",
        "-Dxkb_bin_dir=/usr/bin",
        "-Dxkb_default_rules=base",
        "-Dudev=false",
        "-Dudev_kms=false",
    ),
)
