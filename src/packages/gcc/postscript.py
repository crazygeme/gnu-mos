import os
from pathlib import Path


root = Path(os.environ["LFS_SYSROOT"]) / "usr/bin"
target = os.environ.get("LFS_TARGET", "i686-lfs-linux-gnu")
commands = ("gcc", "g++", "cpp", "cc", "c++")
for command in commands:
    prefixed = root / f"{target}-{command}"
    link = root / command
    if not prefixed.exists():
        continue
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(prefixed.name)
