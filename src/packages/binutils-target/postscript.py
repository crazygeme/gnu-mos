import os
from pathlib import Path

root = Path(os.environ["LFS_SYSROOT"]) / "usr"
target = os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu")
for command in ("as", "ld"):
    for tool in (root / "bin" / command, root / target / "bin" / command):
        if not tool.is_file():
            raise SystemExit(f"target binutils tool missing: {tool}")
