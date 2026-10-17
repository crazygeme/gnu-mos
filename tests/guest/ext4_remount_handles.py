"""Validate open handles and concurrent mapped reads during root remounts."""
import ctypes
import mmap
import os
from pathlib import Path
libc = ctypes.CDLL(None, use_errno=True)
source = Path('/usr/bin/python3').resolve()
with source.open('rb') as handle:
    expected = handle.read(4096)
    workers = []
    for unused in range(4):
        child = os.fork()
        if not child:
            try:
                with source.open('rb') as reader:
                    with mmap.mmap(reader.fileno(), 0, access=mmap.ACCESS_READ) as mapping:
                        for cycle in range(8):
                            for offset in range(0, len(mapping), 4096):
                                value = mapping[offset]
                os._exit(0)
            except BaseException:
                os._exit(1)
        workers.append(child)
    for unused in range(8):
        assert libc.mount(None, b'/', None, 32, None) == 0, ctypes.get_errno()
        handle.seek(0)
        assert handle.read(4096) == expected
    for child in workers:
        assert os.waitpid(child, 0)[1] == 0
print('PASS: ext4 remount retains open handles and concurrent mapped reads')
