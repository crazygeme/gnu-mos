import os
from pathlib import Path

root = Path(os.environ["LFS_SYSROOT"])
runlevel = "3" if os.environ.get("LFS_NO_GUI") == "1" else "5"
inittab = root / "etc/inittab"
lines = inittab.read_text().splitlines()
for index, line in enumerate(lines):
    fields = line.split(":", 3)
    if len(fields) == 4 and fields[2] == "initdefault":
        fields[1] = runlevel
        lines[index] = ":".join(fields)
inittab.write_text("\n".join(lines) + "\n")
