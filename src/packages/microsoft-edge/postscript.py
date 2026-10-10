import os
from pathlib import Path
import shutil
import subprocess

sysroot = Path(os.environ["LFS_SYSROOT"])
directory = sysroot / "opt/microsoft/msedge"
launcher = directory / "microsoft-edge"
wrapper = Path(__file__).with_name("microsoft-edge")
if launcher.read_bytes() != wrapper.read_bytes():
    shutil.copy2(launcher, directory / "microsoft-edge.vendor")
shutil.copyfile(wrapper, launcher)
launcher.chmod(0o755)

for name in ("microsoft-edge", "microsoft-edge-stable"):
    alias = sysroot / "usr/bin" / name
    alias.unlink(missing_ok=True)
    alias.symlink_to("/opt/microsoft/msedge/microsoft-edge")

privileged = [] if os.geteuid() == 0 else ["sudo"]
sandbox = directory / "msedge-sandbox"
subprocess.run(privileged + ["chown", "0:0", str(sandbox)], check=True)
subprocess.run(privileged + ["chmod", "4755", str(sandbox)], check=True)
