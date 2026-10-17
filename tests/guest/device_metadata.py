"""Validate device metadata through O_PATH links and device access checks."""
import errno
import os
from pathlib import Path
import tempfile
with tempfile.TemporaryDirectory(prefix='mos-device-metadata-') as directory:
    os.chmod(directory, 0o755)
    node = Path(directory) / 'null'
    os.mknod(node, 0o020666, os.makedev(1, 3))
    fd = os.open(node, os.O_PATH)
    alias = '/proc/self/fd/%d' % fd
    os.chmod(alias, 0o600)
    os.chown(alias, 1000, 1000)
    st = node.stat()
    assert st.st_mode & 0o7777 == 0o600 and st.st_uid == 1000 and st.st_gid == 1000, st
    pid = os.fork()
    if not pid:
        os.setgid(1000); os.setuid(1000)
        with node.open('wb') as output:
            assert output.write(b'permitted') == 9
        os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0
    os.chown(alias, 0, 0)
    pid = os.fork()
    if not pid:
        os.setgid(1000); os.setuid(1000)
        try:
            os.open(node, os.O_WRONLY)
        except OSError as e:
            os._exit(0 if e.errno == errno.EACCES else 1)
        os._exit(1)
    assert os.waitpid(pid, 0)[1] == 0
    os.close(fd)
    node.unlink()
print('PASS: O_PATH device mode/ownership, owner access, and denied foreign access')
for device, expected in [('/dev/tty0', (4, 0)), ('/dev/tty1', (4, 1)),
                         ('/dev/console', (5, 1)), ('/dev/tty', (5, 0))]:
    descriptor = os.open(device, os.O_PATH)
    try:
        number = os.fstat(descriptor).st_rdev
        assert (os.major(number), os.minor(number)) == expected
    finally:
        os.close(descriptor)
print('PASS: Linux virtual and auxiliary terminal device numbers')
