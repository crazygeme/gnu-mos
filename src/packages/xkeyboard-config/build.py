import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source(
    "xkeyboard-config", "xkeyboard-config-2.43.tar.xz", "xkeyboard-config-2.43"
)
build = Path(os.environ["LFS_WORKSPACE"]) / "build/xkeyboard-config-meson"
subprocess.run(
    ["meson", "setup", str(build), str(source), "--prefix=/usr", "-Dnls=false"],
    check=True,
)
subprocess.run(["meson", "compile", "-C", str(build)], check=True)
subprocess.run(
    ["meson", "install", "-C", str(build), "--destdir", os.environ["LFS_SYSROOT"]],
    check=True,
)
