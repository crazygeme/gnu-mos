"""Validate independent reopen and execution of an unlinked tmpfs file."""
import os
from pathlib import Path
import subprocess
import tempfile
with tempfile.NamedTemporaryFile(dir='/tmp', delete=False) as out:
    name = out.name
    out.write(Path('/usr/bin/true').read_bytes())
os.chmod(name, 0o755)
fd = os.open(name, os.O_RDONLY)
os.unlink(name)
try:
    alias = '/proc/self/fd/%d' % fd
    reopened = os.open(alias, os.O_RDONLY)
    assert os.read(reopened, 4) == b'\x7fELF'
    assert os.lseek(fd, 0, os.SEEK_CUR) == 0
    os.close(reopened)
    subprocess.run([alias], pass_fds=(fd,), check=True)
finally:
    os.close(fd)
print('PASS: unlinked tmpfs descriptor reopen, independent offset, and exec')
