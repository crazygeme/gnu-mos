import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

workspace = Path(os.environ["LFS_WORKSPACE"])
native = workspace / "build/libdisplay-info-native.ini"
native.parent.mkdir(parents=True, exist_ok=True)
native.write_text(
    "[built-in options]\n"
    f"pkg_config_path = ['{workspace / 'tools/lib/pkgconfig'}']\n"
)

meson_install(
    archive_source(
        "libdisplay-info", "libdisplay-info-0.2.0.tar.xz", "libdisplay-info-0.2.0"
    ),
    "libdisplay-info",
    options=("--native-file=" + str(native),),
)
