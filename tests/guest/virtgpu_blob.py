"""Validate Venus DRM parameters, blob bounds, and PRIME resource lifetime."""

import ctypes
import errno
import fcntl
import mmap
import os
import select
import stat
import struct


def ioctl(fd, number, format, *values):
    buffer = bytearray(struct.pack(format, *values))
    command = 0xC0000000 | (len(buffer) << 16) | (ord("d") << 8) | number
    fcntl.ioctl(fd, command, buffer, True)
    return struct.unpack(format, buffer)


def rejected(function, expected):
    try:
        function()
    except OSError as error:
        assert error.errno in (expected if isinstance(expected, tuple) else (expected,)), (error.errno, expected)
    else:
        raise AssertionError("Invalid DRM request was accepted")


fd = os.open("/dev/dri/renderD128", os.O_RDWR | os.O_CLOEXEC)
for parameter in (1, 2, 3, 4, 6):
    value = ctypes.c_uint64()
    ioctl(fd, 0x43, "=QQ", parameter, ctypes.addressof(value))
    assert value.value == 1, (parameter, value.value)
params = (ctypes.c_uint64 * 6)(1, 4, 2, 64, 3, 0)
ioctl(fd, 0x4B, "=IIQ", 3, 0, ctypes.addressof(params))
rejected(lambda: ioctl(fd, 0x4B, "=IIQ", 3, 0, ctypes.addressof(params)), errno.EBUSY)
rejected(lambda: ioctl(fd, 0x4A, "=IIIIQIIQQ", 2, 1, 0, 0, 0, 0, 0, 0, 0), errno.EINVAL)
blob = ioctl(fd, 0x4A, "=IIIIQIIQQ", 2, 1, 0, 0, 4096, 0, 0, 0, 0)
handle = blob[2]
offset = ioctl(fd, 0x41, "=QII", 0, handle, 0)[0]
rejected(lambda: mmap.mmap(fd, 8192, offset=offset), errno.EINVAL)
view = mmap.mmap(fd, 4096, offset=offset)
view[:16] = b"Venus blob probe"
prime = ioctl(fd, 0x2D, "=IIi", handle, os.O_CLOEXEC | os.O_RDWR, -1)[2]
rejected(lambda: mmap.mmap(prime, 4096, flags=mmap.MAP_PRIVATE), (errno.EINVAL, errno.EACCES))
rejected(lambda: mmap.mmap(prime, 4096, prot=mmap.PROT_READ | mmap.PROT_EXEC), (errno.EINVAL, errno.EACCES))
alias = mmap.mmap(prime, 4096)
assert alias[:16] == b"Venus blob probe"
# GEM_CLOSE is an input-only ioctl.
fcntl.ioctl(fd, 0x40086409, struct.pack("=II", handle, 0))
view.close()
os.close(fd)
assert alias[:16] == b"Venus blob probe"
alias[0:4] = b"PASS"
assert alias[0:4] == b"PASS"
alias.close()
os.close(prime)
print("Venus parameters, blob bounds, and PRIME lifetime passed")

# Completed output fences expose metadata through fstat and procfs magic links.
fd = os.open("/dev/dri/renderD128", os.O_RDWR | os.O_CLOEXEC)
fence = ioctl(fd, 0x42, "=IIQQIiIIIIQQ", 2, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0)[5]
metadata = os.fstat(fence)
assert stat.S_ISREG(metadata.st_mode)
assert os.stat(f"/proc/self/fd/{fence}").st_mode == metadata.st_mode
poll = select.poll()
poll.register(fence, select.POLLIN)
assert poll.poll(0) == [(fence, select.POLLIN)]
os.close(fence)
os.close(fd)
print("Completed output fence metadata and readiness passed")

# Legacy VirGL resources cannot supply external memory to a Venus context.
legacy = os.open("/dev/dri/renderD128", os.O_RDWR | os.O_CLOEXEC)
handle = ioctl(legacy, 0x44, "=IIIIIIIIIIIIII", 2, 64, 8, 64, 64,
               1, 1, 0, 0, 0, 0, 0, 0, 0)[10]
prime = ioctl(legacy, 0x2D, "=IIi", handle, os.O_CLOEXEC | os.O_RDWR, -1)[2]
venus = os.open("/dev/dri/renderD128", os.O_RDWR | os.O_CLOEXEC)
ioctl(venus, 0x4B, "=IIQ", 3, 0, ctypes.addressof(params))
rejected(lambda: ioctl(venus, 0x2E, "=IIi", 0, 0, prime), errno.EOPNOTSUPP)
os.close(venus)
os.close(prime)
os.close(legacy)
print("Unsupported legacy VirGL memory import into Venus rejected")

# GPU-only video textures expose complete backing sizes through PRIME.
for format, width, height, minimum in ((64, 640, 368, 640 * 368),
                                       (65, 320, 184, 640 * 184),
                                       (3, 640, 368, 640 * 368 * 4)):
    fd = os.open("/dev/dri/renderD128", os.O_RDWR | os.O_CLOEXEC)
    resource = ioctl(fd, 0x44, "=IIIIIIIIIIIIII", 2, format, 8, width, height,
                     1, 1, 0, 0, 0, 0, 0, 1, 0)
    prime = ioctl(fd, 0x2D, "=IIi", resource[10], os.O_CLOEXEC | os.O_RDWR, -1)[2]
    assert os.fstat(prime).st_size >= minimum
    assert os.lseek(prime, 0, os.SEEK_END) == os.fstat(prime).st_size
    os.close(prime)
    os.close(fd)
print("Video-plane allocation and exported descriptor sizes passed")
