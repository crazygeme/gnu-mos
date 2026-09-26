import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source(
    "dejavu-fonts", "dejavu-fonts-ttf-2.37.tar.bz2", "dejavu-fonts-ttf-2.37"
)
destination = Path(os.environ["LFS_SYSROOT"]) / "usr/share/fonts/dejavu"
destination.mkdir(parents=True, exist_ok=True)
for font in (source / "ttf").glob("*.ttf"):
    shutil.copy2(font, destination / font.name)
