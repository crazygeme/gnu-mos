import os
from pathlib import Path

root = Path(os.environ["LFS_SYSROOT"]) / "usr/bin"
link = root / "pkg-config"
if link.exists() or link.is_symlink():
    link.unlink()
link.symlink_to("pkgconf")
