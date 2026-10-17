"""Validate symbolic links against the visible bind mount path."""
import ctypes
import os
from pathlib import Path
import tempfile
libc = ctypes.CDLL(None, use_errno=True)

def mount(source, path, kind=None, flags=0):
    assert libc.mount(os.fsencode(source) if source else None, os.fsencode(path),
                      os.fsencode(kind) if kind else None, flags, None) == 0, ctypes.get_errno()

assert libc.unshare(0x20000) == 0
mount(None, '/', flags=(1 << 18) | 16384)
with tempfile.TemporaryDirectory(prefix='mos-bind-links-') as directory:
    base = Path(directory)
    source, visible = base / 'source', base / 'visible'
    source.mkdir(); visible.mkdir()
    mount('tmpfs', source, 'tmpfs')
    (source / 'sub').mkdir()
    (source / 'file').write_text('inside')
    (source / 'relative').symlink_to('file')
    (source / 'sub/up').symlink_to('../file')
    (source / 'directory').symlink_to('sub')
    (source / 'escape').symlink_to('../outside')
    (source / 'absolute').symlink_to(base / 'outside')
    (base / 'outside').write_text('outside')
    mount(source, visible, flags=4096)
    assert (visible / 'relative').read_text() == 'inside'
    assert (visible / 'sub/up').read_text() == 'inside'
    assert (visible / 'directory/up').read_text() == 'inside'
    assert (visible / 'escape').read_text() == 'outside'
    assert (visible / 'absolute').read_text() == 'outside'
    for target in [visible, source]:
        assert libc.umount2(os.fsencode(target), 2) == 0, ctypes.get_errno()
        target.rmdir()
    (base / 'outside').unlink()
print('PASS: bind mount relative, intermediate, parent and absolute symbolic links')
