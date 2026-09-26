import os
import tarfile
from pathlib import Path

source = Path(os.environ["LFS_SOURCES"]) / "go1.25.1.linux-amd64.tar.gz"
target = Path(os.environ["LFS_WORKSPACE"]) / "tools/go"
if target.exists():
    raise SystemExit(f"Go host toolchain already exists: {target}")
with tarfile.open(source) as archive:
    archive.extractall(target.parent, filter="data")
