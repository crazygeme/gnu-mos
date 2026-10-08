import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("wqy-microhei", "wqy-microhei-0.2.0-beta.tar.gz", "wqy-microhei")
destination = Path(os.environ["LFS_SYSROOT"]) / "usr/share/fonts/wqy-microhei"
destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(source / "wqy-microhei.ttc", destination)
for license_name in ("LICENSE_Apache2.txt", "LICENSE_GPLv3.txt"):
    shutil.copy2(source / license_name, destination)
