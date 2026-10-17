import json
import os
from pathlib import Path

root = Path(os.environ["LFS_SYSROOT"])
(root / "etc/docker").mkdir(parents=True, exist_ok=True)
configuration = {
    "storage-driver": "vfs",
    "pidfile": "/run/docker.pid",
    "exec-root": "/run/docker",
    "features": {"containerd-snapshotter": False},
    "bridge": "none",
    "iptables": False,
    "ip6tables": False,
    "ip-forward": False,
    "ip-masq": False,
    "exec-opts": ["native.cgroupdriver=systemd"],
    "default-runtime": "mos-runc",
    "runtimes": {
        "mos-runc": {
            "runtimeType": "io.containerd.runc.v2",
            "options": {"NoPivotRoot": True},
        },
    },
}
(root / "etc/docker/daemon.json").write_text(json.dumps(configuration, indent=2) + "\n")
group = root / "etc/group"
entries = group.read_text().splitlines()
if not any(line.startswith("docker:") for line in entries):
    used = {int(line.split(":")[2]) for line in entries if len(line.split(":")) == 4}
    gid = next(number for number in range(990, 1000) if number not in used)
    group.write_text("\n".join(entries) + f"\ndocker:x:{gid}:\n")
    shadow = root / "etc/gshadow"
    shadow.write_text(shadow.read_text().rstrip("\n") + "\ndocker:!::\n")
