import os
from pathlib import Path

helper = Path(os.environ["LFS_SYSROOT"]) / "usr/sbin/unix_chkpwd"
if os.geteuid() == 0:
    os.chown(helper, 0, 0)
helper.chmod(0o4755)
