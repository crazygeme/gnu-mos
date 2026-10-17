"""Validate downstream slave unmounts and recursive unbindable pruning."""
import ctypes
import os
from pathlib import Path
import tempfile
libc = ctypes.CDLL(None, use_errno=True)
NS = 0x20000
REC, BIND = 16384, 4096
PRIVATE, SLAVE, SHARED, UNBINDABLE = 1 << 18, 1 << 19, 1 << 20, 1 << 17

def mount(source, path, kind=None, flags=0):
    assert libc.mount(os.fsencode(source) if source else None, os.fsencode(path),
                      os.fsencode(kind) if kind else None, flags, None) == 0, ctypes.get_errno()
def unmount(path):
    assert libc.umount2(os.fsencode(path), 2) == 0, ctypes.get_errno()
def enter(fd):
    assert libc.setns(fd, NS) == 0, ctypes.get_errno()
def has_mount(path):
    return any(line.split()[4] == str(path) for line in Path('/proc/self/mountinfo').read_text().splitlines())
assert libc.unshare(NS) == 0
mount(None, '/', flags=REC | PRIVATE)
with tempfile.TemporaryDirectory(prefix='mos-propagation-depth-') as directory:
    base = Path(directory) / 'source'
    copy = Path(directory) / 'copy'
    base.mkdir(); copy.mkdir()
    mount('tmpfs', base, 'tmpfs')
    (base / 'incoming').mkdir()
    mount(None, base, flags=SHARED)
    original = os.open('/proc/self/ns/mnt', os.O_RDONLY)
    assert libc.unshare(NS) == 0
    mount(None, base, flags=SLAVE)
    mount(None, base, flags=SHARED)
    middle = os.open('/proc/self/ns/mnt', os.O_RDONLY)
    assert libc.unshare(NS) == 0
    mount(None, base, flags=SLAVE)
    leaf = os.open('/proc/self/ns/mnt', os.O_RDONLY)
    enter(original)
    mount('tmpfs', base / 'incoming', 'tmpfs')
    enter(leaf)
    assert has_mount(base / 'incoming')
    enter(original)
    unmount(base / 'incoming')
    enter(leaf)
    assert not has_mount(base / 'incoming')
    enter(original)
    os.close(middle); os.close(leaf); os.close(original)
    mount(None, base, flags=PRIVATE | REC)
    (base / 'nested').mkdir()
    mount('tmpfs', base / 'nested', 'tmpfs')
    (base / 'nested/hidden').mkdir()
    mount('tmpfs', base / 'nested/hidden', 'tmpfs')
    (base / 'nested/hidden/marker').write_text('unbound')
    mount(None, base / 'nested/hidden', flags=UNBINDABLE)
    mount(base, copy, flags=BIND | REC)
    assert has_mount(copy / 'nested')
    assert not has_mount(copy / 'nested/hidden')
    assert not (copy / 'nested/hidden/marker').exists()
    unmount(copy)
    unmount(base / 'nested/hidden')
    unmount(base / 'nested')
    unmount(base)
    base.rmdir(); copy.rmdir()
print('PASS: downstream slave unmounts and nested unbindable pruning')
