import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"])
wrapper = sysroot / "usr/libexec/Xorg.wrap"
server = sysroot / "usr/libexec/Xorg"
privileged = [] if os.geteuid() == 0 else ["sudo"]

# Boot initialization enables setuid after assigning system file ownership.
subprocess.run(privileged + ["chown", "0:0", str(wrapper), str(server)], check=True)
subprocess.run(privileged + ["chmod", "0755", str(server)], check=True)
subprocess.run(privileged + ["chmod", "0755", str(wrapper)], check=True)

(sysroot / "var/lib/xkb").mkdir(parents=True, exist_ok=True)
for name in (".X11-unix", ".ICE-unix"):
    directory = sysroot / "tmp" / name
    directory.mkdir(parents=True, exist_ok=True)
    subprocess.run(privileged + ["chown", "0:0", str(directory)], check=True)
    subprocess.run(privileged + ["chmod", "1777", str(directory)], check=True)
