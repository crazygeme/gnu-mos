import os
from pathlib import Path
import shutil
import subprocess

sysroot = Path(os.environ["LFS_SYSROOT"])
directory = sysroot / "usr/share/code"
launcher = directory / "code"
with launcher.open("rb") as stream:
    binary = stream.read(4) == b"\x7fELF"
if binary:
    launcher.replace(directory / "code.bin")
shutil.copyfile(Path(__file__).with_name("code"), launcher)
launcher.chmod(0o755)

cli = directory / "bin/code"
if b"exec /usr/share/code/bin/code.vendor" not in cli.read_bytes():
    shutil.copy2(cli, directory / "bin/code.vendor")
shutil.copyfile(Path(__file__).with_name("code-cli"), cli)
cli.chmod(0o755)

privileged = [] if os.geteuid() == 0 else ["sudo"]
sandbox = directory / "chrome-sandbox"
subprocess.run(privileged + ["chown", "0:0", str(sandbox)], check=True)
subprocess.run(privileged + ["chmod", "4755", str(sandbox)], check=True)
