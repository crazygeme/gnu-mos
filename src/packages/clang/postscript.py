"""Configure Clang C and C++ commands and Debian runtime library lookup."""

import json
import os
from pathlib import Path


sysroot = Path(os.environ["LFS_SYSROOT"])
library = sysroot / "usr/lib"
multiarch = library / "x86_64-linux-gnu"
# The target loader searches /usr/lib; Debian payloads retain multiarch paths.
for source in sorted(multiarch.glob("*.so*")):
    alias = library / source.name
    if not alias.exists() and not alias.is_symlink():
        alias.symlink_to(Path("x86_64-linux-gnu") / source.name)

commands = sysroot / "usr/bin"
for name in ("clang", "clang++", "clang-cpp"):
    alias = commands / name
    alias.unlink(missing_ok=True)
    alias.symlink_to(name + "-19")

gcc = json.loads((Path(__file__).parents[1] / "gcc-target/package.json").read_text())
target = os.environ["LFS_TARGET"]
configuration = (
    f"--target={target}\n"
    f"--gcc-install-dir=/usr/lib/gcc/{target}/{gcc['version']}\n"
)
for name in ("clang", "clang++", "clang-cpp"):
    (library / "llvm-19/bin" / (name + ".cfg")).write_text(configuration)
