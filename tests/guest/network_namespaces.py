"""Validate network namespace interfaces, transport isolation, and lifetime."""
import ctypes
import errno
import os
import socket
import fcntl
import struct

libc = ctypes.CDLL(None, use_errno=True)
port = 37431
host_tcp = socket.socket()
host_tcp.bind(('127.0.0.1', port))
host_tcp.listen()
host_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host_udp.bind(('127.0.0.1', port))
host_abstract = socket.socket(socket.AF_UNIX)
host_abstract.bind(b'\0mos-network-test')
host_abstract.listen()
host_only = socket.socket(socket.AF_UNIX)
host_only.bind(b'\0mos-host-only')
host_only.listen()
pid = os.fork()
if not pid:
    try:
        for s in (host_tcp, host_udp, host_abstract, host_only):
            s.close()
        assert libc.unshare(0x40000000) == 0, ctypes.get_errno()
        interfaces = socket.if_nameindex()
        assert [name for _, name in interfaces] == ['lo'], interfaces
        assert 'eth' not in open('/proc/net/dev').read()
        control = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        request = struct.pack('16sH22x', b'lo', 1)
        fcntl.ioctl(control, 0x8914, request)
        abstract = socket.socket(socket.AF_UNIX)
        abstract.bind(b'\0mos-network-test')
        missing = socket.socket(socket.AF_UNIX)
        try:
            missing.connect(b'\0mos-host-only')
            raise AssertionError('abstract socket crossed namespace')
        except OSError as e:
            assert e.errno == errno.ECONNREFUSED, e
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind(('127.0.0.1', port))
        udp.settimeout(3)
        udp.sendto(b'private-udp', ('127.0.0.1', port))
        assert udp.recv(64) == b'private-udp'
        server = socket.socket()
        server.bind(('127.0.0.1', port))
        server.listen()
        client = socket.socket()
        client.settimeout(3)
        client.connect(('127.0.0.1', port))
        accepted, _ = server.accept()
        client.sendall(b'private-tcp')
        assert accepted.recv(64) == b'private-tcp'
        # A socket retains its namespace after the process changes namespaces.
        initial = os.open('/proc/1/ns/net', os.O_RDONLY)
        assert libc.setns(initial, 0x40000000) == 0, ctypes.get_errno()
        assert any(name.startswith('e') for _, name in socket.if_nameindex())
        udp.sendto(b'retained', ('127.0.0.1', port))
        assert udp.recv(64) == b'retained'
        print('PASS: private loopback, TCP/UDP ports, abstract sockets, and retained namespace', flush=True)
    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(1)
    os._exit(0)
assert os.waitpid(pid, 0)[1] == 0
host_udp.setblocking(False)
try:
    host_udp.recv(64)
    raise AssertionError('private UDP reached initial namespace')
except BlockingIOError:
    pass
print('PASS: initial namespace receives no private traffic')
