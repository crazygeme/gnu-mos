import os
from pathlib import Path
import shutil

sysroot = Path(os.environ["LFS_SYSROOT"])
directory = sysroot / "usr/share/code"
launcher = directory / "code"
with launcher.open("rb") as stream:
    binary = stream.read(4) == b"\x7fELF"
if binary:
    launcher.replace(directory / "code.bin")
shutil.copyfile(Path(__file__).with_name("code"), launcher)
launcher.chmod(0o755)
