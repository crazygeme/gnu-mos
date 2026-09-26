import os
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"])
(sysroot / "var/cache/man").mkdir(parents=True, exist_ok=True)
config = sysroot / "usr/etc/man_db.conf"
config.parent.mkdir(parents=True, exist_ok=True)
config.unlink(missing_ok=True)
config.symlink_to("../../etc/man_db.conf")
