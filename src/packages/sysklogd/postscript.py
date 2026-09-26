import os
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"])
log_dir = sysroot / "var/log"
log_dir.mkdir(parents=True, exist_ok=True)
for name in ("auth.log", "kern.log", "messages"):
    log = log_dir / name
    log.touch(exist_ok=True)
    log.chmod(0o640)
