import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"]).resolve()
subprocess.run(
    [
        str(sysroot / "usr/lib/ld-linux.so.2"),
        "--library-path",
        str(sysroot / "usr/lib") + ":" + str(sysroot / "lib"),
        str(sysroot / "usr/bin/glib-compile-schemas"),
        str(sysroot / "usr/share/glib-2.0/schemas"),
    ],
    check=True,
)
