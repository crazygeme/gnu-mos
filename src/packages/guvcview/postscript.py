"""Configure the installed USB camera preview launcher."""
import os
from pathlib import Path
path = Path(os.environ["LFS_SYSROOT"]) / "usr/share/applications/guvcview.desktop"
if path.is_file():
    lines = path.read_text().splitlines()
    lines = ["Exec=guvcview --capture=mmap --format=MJPG --resolution=320x240 --audio=none" if line.startswith("Exec=") else line for line in lines]
    path.write_text("\n".join(lines) + "\n")
