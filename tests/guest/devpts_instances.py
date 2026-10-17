"""Validate devpts instances, metadata-only opens, and terminal data paths."""
import array
import ctypes
import errno
import fcntl
import os
from pathlib import Path
import tempfile
import tty
libc = ctypes.CDLL(None, use_errno=True)
assert libc.unshare(0x20000) == 0
assert libc.mount(None, b'/', None, (1 << 18) | 16384, None) == 0
with tempfile.TemporaryDirectory(prefix='mos-devpts-') as directory:
    paths = [Path(directory) / name for name in ['first', 'second']]
    masters, slaves = [], []
    try:
        for path in paths:
            path.mkdir()
            assert libc.mount(b'devpts', os.fsencode(path), b'devpts', 0,
                              b'newinstance,ptmxmode=0666,mode=0620,gid=5') == 0, ctypes.get_errno()
            descriptor = os.open(path / 'ptmx', os.O_PATH)
            assert set(os.listdir(path)) == {'ptmx'}
            assert os.fstat(descriptor).st_mode & 0o777 == 0o666
            assert os.fstat(descriptor).st_ino == 2
            os.close(descriptor)
            master = os.open(path / 'ptmx', os.O_RDWR | os.O_NOCTTY)
            masters.append(master)
            index = array.array('I', [99])
            fcntl.ioctl(master, 0x80045430, index, True)
            assert index[0] == 0
            lock = array.array('I', [0])
            fcntl.ioctl(master, 0x40045431, lock)
            stat = (path / '0').stat()
            assert stat.st_gid == 5 and stat.st_mode & 0o777 == 0o620
            slave = os.open(path / '0', os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            slaves.append(slave)
            tty.setraw(slave)
        os.write(masters[0], b'first')
        assert os.read(slaves[0], 32) == b'first'
        try:
            os.read(slaves[1], 32)
            raise AssertionError('terminal data crossed devpts instances')
        except BlockingIOError as error:
            assert error.errno == errno.EAGAIN
        os.write(masters[1], b'second')
        assert os.read(slaves[1], 32) == b'second'
        metadata = os.open(paths[0] / '0', os.O_PATH)
        os.close(slaves.pop(0)); os.close(masters.pop(0))
        assert os.fstat(metadata).st_mode & 0o777 == 0o620
        os.close(metadata)
        assert libc.mount(os.fsencode(paths[0]), b'/dev/pts', None, 4096, None) == 0
        try:
            alias = os.open('/dev/ptmx', os.O_RDWR | os.O_NOCTTY)
            try:
                index = array.array('I', [99])
                fcntl.ioctl(alias, 0x80045430, index, True)
                assert index[0] == 0 and (paths[0] / '0').exists()
            finally:
                os.close(alias)
        finally:
            assert libc.umount2(b'/dev/pts', 2) == 0
    finally:
        for descriptor in slaves + masters:
            os.close(descriptor)
        for path in paths:
            assert libc.umount2(os.fsencode(path), 2) == 0, ctypes.get_errno()
            path.rmdir()
print('PASS: independent devpts numbering, terminal data, modes, and descriptor lifetime')
