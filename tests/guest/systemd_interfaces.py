#!/usr/bin/python3
"""Validate timerfd saturation and statx mount identity interfaces."""
import ctypes
import os
import select

libc = ctypes.CDLL(None, use_errno=True)

class Timespec(ctypes.Structure):
    _fields_ = [("sec", ctypes.c_int64), ("nsec", ctypes.c_int64)]

class TimerSpec(ctypes.Structure):
    _fields_ = [("interval", Timespec), ("value", Timespec)]

class StatxTimestamp(ctypes.Structure):
    _fields_ = [("sec", ctypes.c_int64), ("nsec", ctypes.c_uint32),
                ("reserved", ctypes.c_int32)]

class Statx(ctypes.Structure):
    _fields_ = [("mask", ctypes.c_uint32), ("blksize", ctypes.c_uint32),
                ("attributes", ctypes.c_uint64), ("nlink", ctypes.c_uint32),
                ("uid", ctypes.c_uint32), ("gid", ctypes.c_uint32),
                ("mode", ctypes.c_uint16), ("reserved", ctypes.c_uint16),
                ("ino", ctypes.c_uint64), ("size", ctypes.c_uint64),
                ("blocks", ctypes.c_uint64), ("attributes_mask", ctypes.c_uint64),
                ("atime", StatxTimestamp), ("btime", StatxTimestamp),
                ("ctime", StatxTimestamp), ("mtime", StatxTimestamp),
                ("rdev_major", ctypes.c_uint32), ("rdev_minor", ctypes.c_uint32),
                ("dev_major", ctypes.c_uint32), ("dev_minor", ctypes.c_uint32),
                ("mnt_id", ctypes.c_uint64), ("spare", ctypes.c_uint64 * 13)]

assert ctypes.sizeof(Statx) == 256
fd = libc.timerfd_create(0, os.O_NONBLOCK | os.O_CLOEXEC)
assert fd >= 0, ctypes.get_errno()
try:
    timer = TimerSpec(Timespec(0, 0), Timespec(2**63 - 1, 0))
    assert libc.timerfd_settime(fd, 3, ctypes.byref(timer), None) == 0, ctypes.get_errno()
    assert select.select([fd], [], [], 0)[0] == []
    remaining = TimerSpec()
    assert libc.timerfd_gettime(fd, ctypes.byref(remaining)) == 0
    assert remaining.value.sec > 7_000_000_000, remaining.value.sec
finally:
    os.close(fd)

def statx(path):
    result = Statx()
    assert libc.statx(-100, path.encode(), 0, 0x1001, ctypes.byref(result)) == 0, ctypes.get_errno()
    assert result.mask & 0x1000
    assert result.attributes_mask & 0x2000
    return result

root = statx("/")
etc = statx("/etc")
proc = statx("/proc")
assert root.attributes & 0x2000
assert not etc.attributes & 0x2000
assert proc.attributes & 0x2000
assert root.mnt_id == etc.mnt_id
assert root.mnt_id != proc.mnt_id
print("SYSTEMD_INTERFACES_OK")
