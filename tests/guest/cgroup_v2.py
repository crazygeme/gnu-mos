"""Validate the cgroup v2 domain hierarchy and pids controller as root."""
import ctypes
import errno
import os
import select
import subprocess
from pathlib import Path
import tempfile
import time
import traceback

libc = ctypes.CDLL(None, use_errno=True)

def check_call(result):
    if result < 0:
        value = ctypes.get_errno()
        raise OSError(value, os.strerror(value))


def write(group, name, value):
    (group / name).write_text(str(value))


def expect_error(code, action):
    try:
        action()
    except OSError as error:
        assert error.errno == code, (error.errno, code)
    else:
        raise AssertionError('Operation unexpectedly succeeded')


def child(action):
    pid = os.fork()
    if pid == 0:
        try:
            action()
        except BaseException:
            traceback.print_exc()
            os._exit(1)
        os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0


check_call(libc.unshare(0x00020000))  # CLONE_NEWNS
mountpoint = Path(tempfile.mkdtemp(prefix='mos-cgroup2-'))
check_call(libc.mount(b'none', os.fsencode(mountpoint), b'cgroup2', 0, None))
root = mountpoint
parent = root / ('probe-' + str(os.getpid()))
try:
    assert 'cgroup.controllers' in {p.name for p in root.iterdir()}
    assert not (root / 'tasks').exists()
    assert not (root / 'devices.allow').exists()
    assert (root / 'cgroup.type').read_text() == 'domain\n'
    assert '0::' in Path('/proc/self/cgroup').read_text()
    controllers = (root / 'cgroup.controllers').read_text().split()
    assert 'pids' in controllers, 'pids controller is bound to cgroup v1'
    was_enabled = 'pids' in (root / 'cgroup.subtree_control').read_text().split()
    write(root, 'cgroup.subtree_control', '+pids')
    parent.mkdir()
    assert (parent / 'pids.max').read_text() == 'max\n'
    assert (parent / 'cgroup.subtree_control').read_text() == '\n'
    expect_error(errno.EINVAL, lambda: write(parent, 'cgroup.subtree_control', '+pids +invalid'))
    assert (parent / 'cgroup.subtree_control').read_text() == '\n'
    write(parent, 'cgroup.subtree_control', '+pids')
    leaf = parent / 'leaf'
    leaf.mkdir()
    expect_error(errno.EBUSY, lambda: write(root, 'cgroup.subtree_control', '-pids'))
    expect_error(errno.EINVAL, lambda: write(leaf, 'pids.max', '1\njunk'))
    expect_error(errno.EOPNOTSUPP, lambda: write(leaf, 'cgroup.type', 'threaded'))

    def limits():
        expect_error(errno.EBUSY, lambda: write(parent, 'cgroup.procs', 0))
        write(leaf, 'cgroup.procs', 0)
        assert str(os.getpid()) in (leaf / 'cgroup.procs').read_text().split()
        assert str(os.getpid()) in (leaf / 'cgroup.threads').read_text().split()
        assert (parent / 'cgroup.events').read_text() == 'populated 1\n'
        assert (parent / 'pids.current').read_text() == '1\n'
        write(parent, 'pids.max', 1)
        expect_error(errno.EAGAIN, os.fork)
        assert int((leaf / 'pids.events').read_text().split()[1]) >= 1
        write(parent, 'pids.max', 2)
        child(lambda: None)
        write(leaf, 'pids.max', 0)
        expect_error(errno.EAGAIN, os.fork)
        # Migration is permitted above pids.max.
        write(root, 'cgroup.procs', 0)
        write(leaf, 'cgroup.procs', 0)
        check_call(libc.unshare(0x02000000))  # CLONE_NEWCGROUP
        assert '0::/\n' in Path('/proc/self/cgroup').read_text()
        nested = Path(tempfile.mkdtemp(prefix='mos-cgroup2-ns-'))
        check_call(libc.mount(b'none', os.fsencode(nested), b'cgroup2', 0, None))
        assert str(os.getpid()) in (nested / 'cgroup.procs').read_text().split()
        check_call(libc.umount(os.fsencode(nested)))
        nested.rmdir()

    events_fd = os.open(parent / 'cgroup.events', os.O_RDONLY)
    os.read(events_fd, 256)
    events = select.poll()
    events.register(events_fd, select.POLLPRI | select.POLLERR)
    assert events.poll(0) == []
    child(limits)
    assert events.poll(1000), 'Population change did not notify poll'
    os.lseek(events_fd, 0, os.SEEK_SET)
    os.read(events_fd, 256)
    assert events.poll(0) == []
    notifier = os.fork()
    if notifier == 0:
        time.sleep(0.1)
        try:
            write(leaf, 'cgroup.procs', 0)
        except BaseException:
            traceback.print_exc()
            os._exit(1)
        os._exit(0)
    assert events.poll(2000), 'Blocked poll did not wake on population change'
    assert os.waitpid(notifier, 0)[1] == 0
    os.close(events_fd)
    write(parent, 'pids.max', 'max')
    write(leaf, 'pids.max', 'max')
    source = Path(__file__).with_name('cgroup_v2_threads.c')
    executable = '/tmp/mos-cgroup2-threads'
    subprocess.run([os.environ.get('CC', 'gcc'), '-std=gnu99', '-O2', '-Wall',
                    str(source), '-o', executable], check=True)
    pids_fd = os.open(leaf / 'pids.events', os.O_RDONLY)
    os.read(pids_fd, 256)
    events = select.poll()
    events.register(pids_fd, select.POLLPRI | select.POLLERR)
    assert events.poll(0) == []
    subprocess.run([executable, str(leaf)], check=True)
    assert events.poll(1000), 'Pids limit failure did not notify poll'
    os.close(pids_fd)
    os.unlink(executable)
    assert (parent / 'cgroup.events').read_text() == 'populated 0\n'
    held = os.open(leaf / 'cgroup.events', os.O_RDONLY)
    leaf.rmdir()
    assert 'nr_dying_descendants 1\n' in (parent / 'cgroup.stat').read_text()
    os.close(held)
    assert 'nr_dying_descendants 0\n' in (parent / 'cgroup.stat').read_text()
    write(parent, 'cgroup.subtree_control', '-pids')

    delegated = parent / 'delegated'
    delegated.mkdir()
    for name in ('', 'cgroup.procs', 'cgroup.subtree_control'):
        os.chown(delegated / name, 1000, 1000)

    def delegation():
        write(delegated, 'cgroup.procs', 0)
        os.setgid(1000)
        os.setuid(1000)
        sub = delegated / 'child'
        sub.mkdir()
        write(sub, 'cgroup.procs', 0)
        assert sub.stat().st_uid == 1000
        expect_error(errno.EACCES, lambda: write(parent, 'cgroup.procs', 0))
        write(delegated, 'cgroup.procs', 0)
        sub.rmdir()

    sibling = parent / 'outside'
    sibling.mkdir()
    os.chown(sibling / 'cgroup.procs', 1000, 1000)

    def boundary():
        write(delegated, 'cgroup.procs', 0)
        os.setgid(1000)
        os.setuid(1000)
        expect_error(errno.EACCES, lambda: write(sibling, 'cgroup.procs', 0))

    child(boundary)
    sibling.rmdir()
    child(delegation)
    delegated.rmdir()
    parent.rmdir()
    if not was_enabled:
        write(root, 'cgroup.subtree_control', '-pids')
finally:
    check_call(libc.umount(os.fsencode(mountpoint)))
    mountpoint.rmdir()
print('PASS: cgroup v2 hierarchy, pids limits, migration, delegation, and namespaces')
