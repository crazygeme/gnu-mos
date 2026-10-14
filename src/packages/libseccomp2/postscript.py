import os
from pathlib import Path

root = Path(os.environ["LFS_SYSROOT"])
lib = root / "usr/lib"
for path in (lib / "x86_64-linux-gnu").glob("*.so*"):
    alias = lib / path.name
    if not alias.exists() and not alias.is_symlink():
        alias.symlink_to("x86_64-linux-gnu/" + path.name)
