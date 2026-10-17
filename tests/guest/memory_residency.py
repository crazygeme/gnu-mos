"""Validate resident-page queries without faulting the queried mappings."""
import ctypes
import errno
import mmap
import os
import tempfile
libc = ctypes.CDLL(None, use_errno=True)
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
page = mmap.PAGESIZE
address = libc.mmap(None, page * 3, 3, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, -1, 0)
assert address not in (None, ctypes.c_void_p(-1).value)
vec = (ctypes.c_ubyte * 3)()
assert libc.mincore(address, page * 3, vec) == 0
assert list(vec) == [0, 0, 0], list(vec)
ctypes.c_ubyte.from_address(address + page).value = 7
assert libc.mincore(address, page * 3, vec) == 0
assert list(vec) == [0, 1, 0], list(vec)
assert libc.mincore(address + 1, page, vec) == -1 and ctypes.get_errno() == errno.EINVAL
assert libc.munmap(address, page * 3) == 0
assert libc.mincore(address, page, vec) == -1 and ctypes.get_errno() == errno.ENOMEM
with tempfile.TemporaryFile(dir='/tmp') as file:
    file.write(b'x' * page)
    file.flush()
    address = libc.mmap(None, page, 1, mmap.MAP_SHARED, file.fileno(), 0)
    assert libc.mincore(address, page, vec) == 0
    assert vec[0] == 1
    assert libc.munmap(address, page) == 0
print('PASS: anonymous faults, resident tmpfs pages, alignment, and unmapped ranges')
