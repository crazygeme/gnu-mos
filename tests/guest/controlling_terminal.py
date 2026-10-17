"""Validate repeated acquisition of the session's controlling terminal."""
import array
import fcntl
import os
child = os.fork()
if not child:
    try:
        os.setsid()
        master = os.open('/dev/ptmx', os.O_RDWR | os.O_NOCTTY)
        value = array.array('I', [0])
        fcntl.ioctl(master, 0x40045431, value)
        fcntl.ioctl(master, 0x80045430, value, True)
        slave = os.open('/dev/pts/' + str(value[0]), os.O_RDWR)
        fcntl.ioctl(slave, 0x540e, 0)
        fcntl.ioctl(slave, 0x540e, 0)
        assert os.tcgetpgrp(slave) == os.getpgrp()
        os._exit(0)
    except BaseException:
        os._exit(1)
assert os.waitpid(child, 0)[1] == 0
print('PASS: automatic and repeated controlling terminal acquisition')
