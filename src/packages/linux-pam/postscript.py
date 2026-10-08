import os
import subprocess
from pathlib import Path

helper = Path(os.environ["LFS_SYSROOT"]) / "usr/sbin/unix_chkpwd"
privileged = [] if os.geteuid() == 0 else ["sudo"]
subprocess.run(privileged + ["chown", "0:0", str(helper)], check=True)
subprocess.run(privileged + ["chmod", "4755", str(helper)], check=True)
