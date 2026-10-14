import os
from pathlib import Path

root = Path(os.environ["LFS_SYSROOT"])
for name in ("iptables", "iptables-save", "iptables-restore", "ip6tables", "ip6tables-save", "ip6tables-restore"):
    alias = root / "usr/sbin" / name
    alias.unlink(missing_ok=True)
    alias.symlink_to(name + "-nft")
