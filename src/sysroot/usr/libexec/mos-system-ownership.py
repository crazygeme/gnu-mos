#!/usr/bin/python3
"""Assign root ownership and permissions to privileged system programs."""

import os
from pathlib import Path
import stat

wrapper = Path("/usr/libexec/Xorg.wrap")
sudo = Path("/usr/bin/sudo")
if wrapper.exists() or sudo.exists():
    for root in (Path("/usr"), Path("/etc")):
        attributes = root.stat()
        if (
            attributes.st_uid == 0
            and attributes.st_gid == 0
            and not attributes.st_mode & 0o022
        ):
            continue
        # Protect children before marking the directory tree as initialized.
        for directory, subdirectories, files in os.walk(root, topdown=False):
            for name in files + subdirectories:
                path = Path(directory) / name
                if path.is_symlink():
                    continue
                mode = stat.S_IMODE(path.stat().st_mode) & ~0o022
                os.chown(path, 0, 0)
                os.chmod(path, mode)
        os.chown(root, 0, 0)
        os.chmod(root, stat.S_IMODE(attributes.st_mode) & ~0o022)
    os.chown("/", 0, 0)
    os.chmod("/", 0o755)
    if wrapper.exists():
        os.chown(wrapper, 0, 0)
        os.chmod(wrapper, 0o4755)
    if sudo.exists():
        for name, mode in (("/var/lib/sudo", 0o711), ("/var/lib/sudo/lectured", 0o700)):
            directory = Path(name)
            directory.mkdir(parents=True, exist_ok=True)
            os.chown(directory, 0, 0)
            os.chmod(directory, mode)
        policy = Path("/etc/sudoers")
        os.chown(policy, 0, 0)
        os.chmod(policy, 0o440)
        os.chown(sudo, 0, 0)
        os.chmod(sudo, 0o4755)

helper = Path("/usr/libexec/dbus-daemon-launch-helper")
if helper.exists():
    import grp
    os.chown(helper, 0, grp.getgrnam("messagebus").gr_gid)
    os.chmod(helper, 0o4750)
for name in ("/usr/bin/pkexec", "/usr/lib/polkit-1/polkit-agent-helper-1"):
    helper = Path(name)
    if helper.exists():
        os.chown(helper, 0, 0)
        os.chmod(helper, 0o4755)
if Path("/usr/lib/polkit-1/polkitd").exists():
    import grp
    import pwd
    uid = pwd.getpwnam("polkitd").pw_uid
    gid = grp.getgrnam("polkitd").gr_gid
    state = Path("/var/lib/polkit-1")
    state.mkdir(parents=True, exist_ok=True)
    os.chown(state, uid, gid)
    os.chmod(state, 0o700)
    for name in ("/etc/polkit-1/rules.d", "/usr/share/polkit-1/rules.d"):
        directory = Path(name)
        directory.mkdir(parents=True, exist_ok=True)
        os.chown(directory, 0, gid)
        os.chmod(directory, 0o750)
