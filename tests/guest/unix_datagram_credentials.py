#!/usr/bin/python3
"""Validate datagram credentials, addressing, peeking, and descriptor passing."""
import array
import os
import socket
import struct
import tempfile

with tempfile.TemporaryDirectory(prefix='mos-unix-credentials-') as directory:
    address = directory + '/receiver'
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as receiver:
        receiver.bind(address)
        receiver.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        children = []
        for index in range(2):
            child = os.fork()
            if child == 0:
                with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender:
                    sender.bind(directory + '/sender-' + str(index))
                    sender.sendto(str(index).encode(), address)
                os._exit(0)
            children.append(child)
        seen = set()
        for index in range(2):
            peek = receiver.recvmsg(32, socket.CMSG_SPACE(12), socket.MSG_PEEK)
            message = receiver.recvmsg(32, socket.CMSG_SPACE(12))
            assert peek == message, (peek, message)
            payload, ancillary, flags, sender = message
            credentials = [struct.unpack('3i', data) for level, kind, data in ancillary
                           if level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS]
            assert len(credentials) == 1
            pid, uid, gid = credentials[0]
            assert pid in children and uid == os.getuid() and gid == os.getgid()
            assert sender == directory + '/sender-' + payload.decode()
            seen.add(pid)
        assert seen == set(children)
        for child in children:
            assert os.waitpid(child, 0)[1] == 0

left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
try:
    right.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    read_fd, write_fd = os.pipe()
    try:
        left.sendmsg([b'F'], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                              array.array('i', [write_fd]))])
        data, control, flags, _ = right.recvmsg(1, socket.CMSG_SPACE(12) + socket.CMSG_SPACE(4))
        assert data == b'F' and not flags & socket.MSG_CTRUNC
        rights = [struct.unpack('i', value)[0] for level, kind, value in control
                  if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS]
        assert len(rights) == 1
        try:
            os.write(rights[0], b'OK')
            assert os.read(read_fd, 2) == b'OK'
        finally:
            os.close(rights[0])
    finally:
        os.close(read_fd)
        os.close(write_fd)
finally:
    left.close()
    right.close()
print('UNIX_DATAGRAM_CREDENTIALS_OK')
