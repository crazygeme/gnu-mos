import os
from pathlib import Path
root = Path(os.environ["LFS_SYSROOT"])
(root / "etc/init.d").mkdir(parents=True, exist_ok=True)
(root / "etc/rcS.d").mkdir(parents=True, exist_ok=True)
(root / "etc/inittab").write_text("id:3:initdefault:\nsi::sysinit:/etc/rcS\nco:2345:respawn:/bin/bash\n")
(root / "etc/rcS").write_text("#!/bin/sh\nmount -a 2>/dev/null || true\nmkdir -p /run /tmp /dev/pts /proc\n")
(root / "sbin/init").write_text("#!/bin/sh\nexec /sbin/telinit 3\n")
(root / "sbin/telinit").write_text("#!/bin/sh\n/etc/rcS\nexec /bin/sh\n")
for path in (root / "etc/rcS", root / "sbin/init", root / "sbin/telinit"):
    path.chmod(0o755)
