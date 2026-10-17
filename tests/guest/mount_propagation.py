#!/usr/bin/python3
"""Validate shared, slave, private, and unbindable mount propagation."""
import ctypes
import os
from pathlib import Path
import tempfile
import traceback

libc = ctypes.CDLL(None, use_errno=True)
BIND, REC = 4096, 16384
PRIVATE, SLAVE, SHARED, UNBINDABLE = 1 << 18, 1 << 19, 1 << 20, 1 << 17

def mount(source, target, kind=None, flags=0):
    result = libc.mount(os.fsencode(source) if source else None, os.fsencode(target),
                        os.fsencode(kind) if kind else None, flags, None)
    assert result == 0, (source, target, flags, ctypes.get_errno())

def unmount(target):
    assert libc.umount2(os.fsencode(target), 2) == 0, ctypes.get_errno()

def mounted(path):
    encoded = str(path)
    return any(line.split()[4] == encoded for line in Path('/proc/self/mountinfo').read_text().splitlines())

with tempfile.TemporaryDirectory(prefix='mos-propagation-') as directory:
    base = Path(directory)
    mount('tmpfs', base, 'tmpfs')
    try:
        mount(None, base, flags=SHARED)
        for name in ('parent', 'child', 'incoming', 'private', 'unbindable', 'copy'):
            (base / name).mkdir()
        parent_read, child_write = os.pipe()
        child_read, parent_write = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(parent_read); os.close(parent_write)
            try:
                assert libc.unshare(0x20000) == 0, ctypes.get_errno()
                os.write(child_write, b'R')
                assert os.read(child_read, 1) == b'A'
                assert mounted(base / 'parent')
                mount('tmpfs', base / 'child', 'tmpfs')
                os.write(child_write, b'A')
                assert os.read(child_read, 1) == b'B'
                assert not mounted(base / 'parent')
                mount(None, base, flags=SLAVE | REC)
                mount('tmpfs', base / 'private', 'tmpfs')
                os.write(child_write, b'B')
                assert os.read(child_read, 1) == b'C'
                assert mounted(base / 'incoming')
                mount(None, base, flags=PRIVATE | REC)
                os.write(child_write, b'C')
                assert os.read(child_read, 1) == b'D'
                assert not mounted(base / 'parent')
                os.write(child_write, b'D')
                os._exit(0)
            except BaseException:
                traceback.print_exc(); os._exit(1)
        os.close(child_write); os.close(child_read)
        try:
            assert os.read(parent_read, 1) == b'R'
            mount('tmpfs', base / 'parent', 'tmpfs')
            os.write(parent_write, b'A')
            assert os.read(parent_read, 1) == b'A'
            assert mounted(base / 'child')
            unmount(base / 'parent')
            os.write(parent_write, b'B')
            assert os.read(parent_read, 1) == b'B'
            assert not mounted(base / 'private')
            mount('tmpfs', base / 'incoming', 'tmpfs')
            os.write(parent_write, b'C')
            assert os.read(parent_read, 1) == b'C'
            mount('tmpfs', base / 'parent', 'tmpfs')
            os.write(parent_write, b'D')
            assert os.read(parent_read, 1) == b'D'
            assert os.waitpid(child, 0)[1] == 0
        finally:
            os.close(parent_read); os.close(parent_write)
        mount('tmpfs', base / 'unbindable', 'tmpfs')
        mount(None, base / 'unbindable', flags=UNBINDABLE)
        assert libc.mount(os.fsencode(base / 'unbindable'), os.fsencode(base / 'copy'), None, BIND, None) < 0
        for name in ('parent', 'child', 'incoming', 'unbindable'):
            if mounted(base / name): unmount(base / name)
    finally:
        unmount(base)
print('MOUNT_PROPAGATION_OK')
