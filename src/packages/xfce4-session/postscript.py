import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"]).resolve()
loader = (
    "ld-linux-x86-64.so.2" if os.environ.get("LFS_ARCH") == "x64" else "ld-linux.so.2"
)
subprocess.run(
    [
        str(sysroot / "usr/lib" / loader),
        "--library-path",
        str(sysroot / "usr/lib") + ":" + str(sysroot / "lib"),
        str(sysroot / "usr/bin/glib-compile-schemas"),
        str(sysroot / "usr/share/glib-2.0/schemas"),
    ],
    check=True,
)
