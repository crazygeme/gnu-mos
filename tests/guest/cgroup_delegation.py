"""Validate cgroup ownership and unprivileged subtree management."""
import os
from pathlib import Path
root = Path('/sys/fs/cgroup/systemd/mos-delegation-test')
root.mkdir()
try:
    for name in ('', 'tasks', 'cgroup.procs'):
        os.chown(root / name, 1000, 1000)
    pid = os.fork()
    if not pid:
        try:
            os.setgid(1000)
            os.setuid(1000)
            child = root / 'child'
            child.mkdir()
            assert child.stat().st_uid == 1000
            (child / 'cgroup.procs').write_text(str(os.getpid()))
            assert str(os.getpid()) in (child / 'cgroup.procs').read_text().split()
            (root / 'cgroup.procs').write_text(str(os.getpid()))
            child.rmdir()
        except BaseException:
            import traceback
            traceback.print_exc()
            os._exit(1)
        os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0
finally:
    root.rmdir()
print('PASS: cgroup ownership, delegated creation, task movement, and removal')
