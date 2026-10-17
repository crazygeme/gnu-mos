"""Validate tmpfs root identity, mount options, and parent traversal."""
import ctypes
import errno
import os
from pathlib import Path
libc = ctypes.CDLL(None, use_errno=True)
assert libc.unshare(0x20000) == 0, ctypes.get_errno()
assert libc.mount(None, b'/', None, (1 << 18) | 16384, None) == 0
root = Path('/tmp/mos-tmpfs-root-test')
root.mkdir(exist_ok=True)
assert libc.mount(b'tmpfs', bytes(root), b'tmpfs', 0, b'mode=0700,uid=1000,gid=1000') == 0
st = root.stat()
assert st.st_mode & 0o7777 == 0o700 and st.st_uid == 1000 and st.st_gid == 1000, st
for path in (str(root), str(root) + '/'):
    try:
        os.mkdir(path, 0o755)
        raise AssertionError('mkdir succeeded for mounted root')
    except OSError as e:
        assert e.errno == errno.EEXIST, e
assert root.stat().st_mode & 0o7777 == 0o700
nested = root
for index in range(8):
    nested = nested / ('component-%d-' % index + 'x' * 36)
    nested.mkdir()
link = nested / 'unit.service'
link.symlink_to('/usr/lib/systemd/system/dbus.service')
assert os.readlink(link) == '/usr/lib/systemd/system/dbus.service'
assert libc.umount2(bytes(root), 2) == 0
root.rmdir()
print('PASS: tmpfs mount ownership, root EEXIST, long parent paths, and symlinks')
