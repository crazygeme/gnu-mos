"""Expose the configured Clang utilities through unversioned command names."""

import os
from pathlib import Path


sysroot = Path(os.environ["LFS_SYSROOT"])
commands = sysroot / "usr/bin"
for source in sorted((sysroot / "usr/lib/llvm-19/bin").iterdir()):
    if source.name in ("clang", "clang++", "clang-cpp", "clang-19"):
        continue
    if not source.is_file() or not os.access(source, os.X_OK):
        continue
    alias = commands / source.name
    alias.unlink(missing_ok=True)
    alias.symlink_to(Path("../lib/llvm-19/bin") / source.name)
