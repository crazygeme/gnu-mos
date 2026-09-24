import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("sysvinit", "sysvinit-3.14.tar.gz", "sysvinit-3.14")
root = Path(os.environ["LFS_SYSROOT"])
env = environment()
make_vars = (
    "VERSION=3.14",
    "CC=" + env["CC"],
    "CFLAGS=" + env["CFLAGS"],
    "LDFLAGS=" + env["LDFLAGS"],
)
subprocess.run(
    [
        "make",
        "-C",
        "src",
        "-j" + str(os.cpu_count() or 1),
        *make_vars,
        "init",
        "runlevel",
        "shutdown",
        "halt",
        "killall5",
    ],
    cwd=source,
    env=env,
    check=True,
)
target = root / "usr/sbin"
target.mkdir(parents=True, exist_ok=True)
for program in ("init", "runlevel", "shutdown", "halt", "killall5"):
    subprocess.run(
        ["install", "-m755", str(source / "src" / program), str(target / program)],
        check=True,
    )
for name, program in (("telinit", "init"), ("reboot", "halt"), ("poweroff", "halt")):
    link = target / name
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(program)
