import os, shutil, subprocess
from pathlib import Path

mos = Path(os.environ["LFS_SOURCES"]) / "mos"
if not (mos / "Makefile").exists():
    raise SystemExit(f"MOS checkout missing: {mos}; run ./lfs fetch")
subprocess.run(
    ["make", "-j4", "ARCH=x86", "BUILD=release"],
    cwd=mos,
    check=True,
)
target = Path(os.environ["LFS_SYSROOT"]) / "boot/kernel"
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(mos / "out/x86/release/kernel", target)
