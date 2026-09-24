import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("sysvinit", "sysvinit-3.14.tar.gz", "sysvinit-3.14")
root = Path(os.environ["LFS_SYSROOT"])
env = environment()
make_vars = ("VERSION=3.14", "CC=" + env["CC"], "CFLAGS=" + env["CFLAGS"],
             "LDFLAGS=" + env["LDFLAGS"])
subprocess.run(
    ["make", "-C", "src", "-j" + str(os.cpu_count() or 1), *make_vars,
     "init", "runlevel", "shutdown", "halt", "killall5"],
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

etc = root / "etc"
etc.mkdir(parents=True, exist_ok=True)
(etc / "inittab").write_text(
    "id:3:initdefault:\n"
    "si::sysinit:/etc/init.d/rcS\n"
    "c1:3:respawn:/etc/init.d/console\n"
    "ca::ctrlaltdel:/sbin/shutdown -r now\n",
    encoding="ascii",
)
init_dir = etc / "init.d"
init_dir.mkdir(parents=True, exist_ok=True)
rcs = init_dir / "rcS"
rcs.write_text(
    "#!/bin/sh\n"
    "export PATH=/sbin:/bin:/usr/sbin:/usr/bin\n"
    "mount -o remount,rw /\n"
    "mount -t proc proc /proc\n"
    "mount -t tmpfs tmpfs /run\n",
    encoding="ascii",
)
rcs.chmod(0o755)
console = init_dir / "console"
console.write_text(
    "#!/bin/sh\n"
    "export PATH=/sbin:/bin:/usr/sbin:/usr/bin\n"
    "export HOME=/root TERM=linux\n"
    "exec /bin/bash -l </dev/tty1 >/dev/tty1 2>&1\n",
    encoding="ascii",
)
console.chmod(0o755)
(etc / "fstab").write_text(
    "/dev/hda1 / ext4 defaults 0 1\n"
    "proc /proc proc defaults 0 0\n"
    "tmpfs /run tmpfs defaults 0 0\n",
    encoding="ascii",
)
