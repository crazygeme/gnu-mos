"""Validate that unmount propagation is controlled by the parent mount."""
import ctypes
import os
from pathlib import Path
import tempfile
libc = ctypes.CDLL(None, use_errno=True)
NS, REC, PRIVATE, SHARED = 0x20000, 16384, 1 << 18, 1 << 20

def mount(source, path, kind=None, flags=0):
    assert libc.mount(os.fsencode(source) if source else None, os.fsencode(path),
                      os.fsencode(kind) if kind else None, flags, None) == 0, ctypes.get_errno()

def enter(fd):
    assert libc.setns(fd, NS) == 0, ctypes.get_errno()

assert libc.unshare(NS) == 0
mount(None, '/', flags=PRIVATE | REC)
with tempfile.TemporaryDirectory(prefix='mos-unmount-isolation-') as directory:
    target = Path(directory) / 'mount'
    target.mkdir()
    mount('tmpfs', target, 'tmpfs')
    (target / 'marker').write_text('retained')
    mount(None, target, flags=SHARED)
    original = os.open('/proc/self/ns/mnt', os.O_RDONLY)
    assert libc.unshare(NS) == 0
    assert libc.umount2(os.fsencode(target), 2) == 0, ctypes.get_errno()
    assert not (target / 'marker').exists()
    enter(original)
    assert (target / 'marker').read_text() == 'retained'
    os.close(original)
    assert libc.umount2(os.fsencode(target), 2) == 0, ctypes.get_errno()
    target.rmdir()
print('PASS: shared child unmount remains isolated under a private parent')
