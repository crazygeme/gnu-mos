import json
import os
from pathlib import Path
import shutil

root = Path(os.environ["LFS_SYSROOT"])
package = Path(__file__).parent
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
    "exec-opts": ["native.cgroupdriver=cgroupfs"],
    "default-runtime": "mos-runc",
    "runtimes": {
        "mos-runc": {
            "runtimeType": "io.containerd.runc.v2",
            "options": {"NoPivotRoot": True},
        },
    },
}
(root / "etc/docker/daemon.json").write_text(json.dumps(configuration, indent=2) + "\n")
script = root / "etc/init.d/docker"
shutil.copyfile(package / "docker.init", script)
script.chmod(0o755)
runlevel = root / "etc/rc3.d"
runlevel.mkdir(parents=True, exist_ok=True)
startup = runlevel / "S45docker"
if startup.is_symlink() or startup.exists():
    startup.unlink()
startup.symlink_to("../init.d/docker")

group = root / "etc/group"
entries = group.read_text().splitlines()
if not any(line.startswith("docker:") for line in entries):
    used = {int(line.split(":")[2]) for line in entries if len(line.split(":")) == 4}
    gid = next(number for number in range(990, 1000) if number not in used)
    group.write_text("\n".join(entries) + f"\ndocker:x:{gid}:\n")
    shadow = root / "etc/gshadow"
    shadow.write_text(shadow.read_text().rstrip("\n") + "\ndocker:!::\n")
