import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"])
privileged = [] if os.geteuid() == 0 else ["sudo"]
for name, mode in (("usr/bin/sudo", "4755"), ("etc/sudoers", "0440")):
    path = sysroot / name
    subprocess.run(privileged + ["chown", "0:0", str(path)], check=True)
    subprocess.run(privileged + ["chmod", mode, str(path)], check=True)

for name, mode in (("var/lib/sudo", "0711"), ("var/lib/sudo/lectured", "0700")):
    path = sysroot / name
    subprocess.run(privileged + ["mkdir", "-p", str(path)], check=True)
    subprocess.run(privileged + ["chown", "0:0", str(path)], check=True)
    subprocess.run(privileged + ["chmod", mode, str(path)], check=True)
