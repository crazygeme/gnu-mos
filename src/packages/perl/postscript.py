import os
from pathlib import Path


root = Path(os.environ["LFS_SYSROOT"]) / "usr/bin"
perl = root / "perl"
if not perl.exists() and not perl.is_symlink():
    candidates = sorted(root.glob("perl5.*"))
    if candidates:
        perl.symlink_to(candidates[0].name)
