#!/usr/bin/python3
"""Validate runtime file allocation, links, descriptor metadata, and recursive bind mounts."""
import ctypes
import os
from pathlib import Path
import stat
import tempfile
import traceback

libc = ctypes.CDLL(None, use_errno=True)
libc.fallocate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int64, ctypes.c_int64]
with tempfile.TemporaryDirectory(prefix='mos-runtime-') as directory:
    first = Path(directory) / 'first'
    second = Path(directory) / 'second'
    fd = os.open(first, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        os.write(fd, b'payload')
        os.chmod('/proc/self/fd/' + str(fd), 0o640)
        assert stat.S_IMODE(os.fstat(fd).st_mode) == 0o640
        os.link(first, second)
        assert os.stat(first).st_ino == os.stat(second).st_ino
        assert os.fstat(fd).st_nlink == 2
        first.unlink()
        assert os.stat(second).st_nlink == 1 and second.read_bytes() == b'payload'
        assert libc.fallocate(fd, 1, 4096, 8192) == 0, ctypes.get_errno()
        assert os.fstat(fd).st_size == 7
        assert os.fstat(fd).st_blocks >= 16
        assert libc.fallocate(fd, 0, 8192, 8192) == 0, ctypes.get_errno()
        assert os.fstat(fd).st_size == 16384
        assert os.pread(fd, 7, 0) == b'payload'
        assert os.pread(fd, 8192, 8192) == b'\0' * 8192
    finally:
        os.close(fd)
assert os.statvfs('/run').f_bavail > 0
if os.geteuid() == 0:
    with tempfile.TemporaryDirectory(prefix='mos-recursive-bind-') as directory:
        child = os.fork()
        if child == 0:
            try:
                assert libc.unshare(0x20000) == 0, ctypes.get_errno()
                assert libc.mount(b'/', os.fsencode(directory), None, 4096 | 16384, None) == 0, ctypes.get_errno()
                try:
                    assert (Path(directory) / 'proc/cmdline').read_bytes() == Path('/proc/cmdline').read_bytes()
                    assert (Path(directory) / 'proc/sys/kernel/random/boot_id').read_bytes() == Path('/proc/sys/kernel/random/boot_id').read_bytes()
                finally:
                    assert libc.umount2(os.fsencode(directory), 2) == 0, ctypes.get_errno()
                os._exit(0)
            except BaseException:
                traceback.print_exc()
                os._exit(1)
        assert os.waitpid(child, 0)[1] == 0
print('RUNTIME_FILESYSTEMS_OK')
