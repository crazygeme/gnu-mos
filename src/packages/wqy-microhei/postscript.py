import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"]).resolve()
loader_name = "ld-linux-x86-64.so.2" if os.environ["LFS_ARCH"] == "x64" else "ld-linux.so.2"
subprocess.run(
    [str(sysroot / "usr/lib" / loader_name), "--library-path",
     f"{sysroot / 'usr/lib'}:{sysroot / 'lib'}", str(sysroot / "usr/bin/fc-cache"),
     "--sysroot=" + str(sysroot), "--force"],
    check=True,
)
