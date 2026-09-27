import os
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"])
(sysroot / "etc/skel").mkdir(parents=True, exist_ok=True)
