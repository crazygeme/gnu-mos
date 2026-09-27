#!/usr/bin/python3
"""Assign root ownership to the system files used by privileged Xorg."""

import os
from pathlib import Path
import stat

wrapper = Path("/usr/libexec/Xorg.wrap")
if wrapper.exists():
    for root in (Path("/usr"), Path("/etc")):
        attributes = root.stat()
        if attributes.st_uid == 0 and attributes.st_gid == 0 and not attributes.st_mode & 0o022:
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
    os.chown(wrapper, 0, 0)
    os.chmod(wrapper, 0o4755)
