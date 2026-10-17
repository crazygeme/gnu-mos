"""Configure native system and session service management."""
import os
from pathlib import Path
import shutil

root = Path(os.environ["LFS_SYSROOT"])
units = root / "etc/systemd/system"
units.mkdir(parents=True, exist_ok=True)

def link(path, target):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.is_file():
        path.unlink()
    path.symlink_to(target)

for name in ("init", "halt", "poweroff", "reboot", "shutdown", "telinit", "runlevel"):
    link(root / "usr/sbin" / name,
         "../lib/systemd/systemd" if name == "init" else "../bin/systemctl")
for name in ("dbus", "sshd", "scron", "docker"):
    link(units / "multi-user.target.wants" / (name + ".service"), "../" + name + ".service")
link(units / "sysinit.target.wants/mos-system-ownership.service", "../mos-system-ownership.service")
link(units / "getty.target.wants/getty@tty1.service", "/usr/lib/systemd/system/getty@.service")
link(units / "graphical.target.wants/xdm.service", "../xdm.service")
link(units / "display-manager.service", "xdm.service")
link(units / "default.target", "/usr/lib/systemd/system/" +
     ("multi-user.target" if os.environ.get("LFS_NO_GUI") == "1" else "graphical.target"))
for name in ("inittab", "init.d", "rc3.d"):
    path = root / "etc" / name
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
for name in ("libasound_module_pcm_oss.so", "libasound_module_ctl_oss.so"):
    (root / "usr/lib/alsa-lib" / name).unlink(missing_ok=True)
for path in (root / "etc/alsa/conf.d").glob("*oss*"):
    path.unlink()

for name, destination in (("run", "../run"), ("lock", "../run/lock")):
    path = root / "var" / name
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    link(path, destination)
