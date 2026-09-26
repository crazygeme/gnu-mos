import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"])
ssh_dir = sysroot / "etc/ssh"
ssh_dir.mkdir(parents=True, exist_ok=True)


def set_attributes(path: Path, mode: str) -> None:
    # Preserve root ownership when setup runs without privilege.
    if os.geteuid() == 0:
        os.chown(path, 0, 0)
        os.chmod(path, int(mode, 8))
    elif path.stat().st_uid == os.geteuid():
        os.chmod(path, int(mode, 8))


privsep_dir = sysroot / "var/empty"
privsep_dir.mkdir(parents=True, exist_ok=True)
set_attributes(privsep_dir, "755")

# The target libc's utmpx implementation uses this file for active login
# records.  OpenSSH records the PTY login before starting the session shell.
utmpx_file = sysroot / "var/run/utmpx"
utmpx_file.parent.mkdir(parents=True, exist_ok=True)
if not utmpx_file.exists():
    utmpx_file.touch()
set_attributes(utmpx_file, "664")

for key_type in ("ed25519", "ecdsa", "rsa"):
    private_key = ssh_dir / f"ssh_host_{key_type}_key"
    public_key = ssh_dir / f"ssh_host_{key_type}_key.pub"
    if private_key.exists() and private_key.stat().st_size == 0:
        private_key.unlink()
    if not private_key.is_file():
        subprocess.run(
            ["ssh-keygen", "-q", "-t", key_type, "-N", "", "-f", str(private_key)],
            check=True,
        )
    set_attributes(private_key, "600")
    if public_key.is_file():
        public_key.chmod(0o644)
