import os
import shutil
import subprocess
from pathlib import Path

mos = Path(os.environ["LFS_SOURCES"]) / "mos"
if not (mos / "Makefile").exists():
    raise SystemExit(f"MOS checkout missing: {mos}; run ./lfs fetch")
build = Path(os.environ["LFS_WORKSPACE"]) / "build/mos"
if build.exists():
    shutil.rmtree(build)
build.mkdir(parents=True)
# Snapshot tracked and non-ignored source files, including working-tree edits.
paths = subprocess.check_output(
    [
        "git",
        "-C",
        str(mos),
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ]
).split(b"\0")
for raw_path in paths:
    if not raw_path:
        continue
    relative = Path(os.fsdecode(raw_path))
    source = mos / relative
    if not source.exists() and not source.is_symlink():
        continue
    target = build / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target, follow_symlinks=False)
arch = os.environ.get("LFS_ARCH", "x86")
subprocess.run(
    ["make", "-j4", "ARCH=" + arch, "BUILD=release"],
    cwd=build,
    check=True,
)
target = Path(os.environ["LFS_SYSROOT"]) / "boot/kernel"
target.parent.mkdir(parents=True, exist_ok=True)
kernel = "kernel.boot" if arch == "x64" else "kernel"
shutil.copy2(build / "out" / arch / "release" / kernel, target)
