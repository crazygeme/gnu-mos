import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("neofetch", "neofetch-7.1.0.tar.gz", "neofetch-7.1.0")
subprocess.run(
    ["patch", "--batch", "--forward", "-p1", "-i",
     str(Path(__file__).with_name("mos-kernel.patch"))],
    cwd=source,
    check=True,
)
prefix = Path(os.environ["LFS_SYSROOT"]) / "usr"
for name, relative, mode in (
    ("neofetch", "bin/neofetch", 0o755),
    ("neofetch.1", "share/man/man1/neofetch.1", 0o644),
    ("LICENSE.md", "share/licenses/neofetch/LICENSE.md", 0o644),
):
    destination = prefix / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / name, destination)
    destination.chmod(mode)
