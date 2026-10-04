import os
import shutil
from pathlib import Path

if os.environ.get("LFS_NO_GUI", "0") == "1":
    raise SystemExit(0)

applications = Path(os.environ["LFS_SYSROOT"]) / "usr/share/applications"
applications.mkdir(parents=True, exist_ok=True)
shutil.copy2(
    Path(__file__).with_name("ffplay.desktop"), applications / "ffplay.desktop"
)
