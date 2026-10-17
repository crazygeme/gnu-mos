#!/usr/bin/python3
"""Validate mounted filesystem identities and preferred block sizes."""
import os

paths = ("/", "/usr", "/etc", "/bin/sh")
identity = os.stat("/").st_dev
for path in paths:
    state = os.stat(path)
    assert state.st_dev == identity, (path, state.st_dev, identity)
    assert state.st_blksize >= 512, (path, state.st_blksize)
assert os.stat("/proc").st_dev != identity
assert os.path.isfile("/proc/cmdline")
assert open("/proc/cmdline").read().endswith("\n")
print("FILESYSTEM_IDENTITY_OK")
