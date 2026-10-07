import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source(
    "ca-certificates", "ca-certificates_20260816.tar.xz", "ca-certificates"
)
mozilla = source / "mozilla"
subprocess.run(["/usr/bin/python3", "certdata2pem.py"], cwd=mozilla, check=True)
root = Path(os.environ["LFS_SYSROOT"])
certificates = root / "usr/share/ca-certificates/mozilla"
certificates.mkdir(parents=True, exist_ok=True)
bundle = root / "etc/ssl/certs/ca-certificates.crt"
bundle.parent.mkdir(parents=True, exist_ok=True)
with bundle.open("wb") as output:
    for certificate in sorted(mozilla.glob("*.crt")):
        shutil.copyfile(certificate, certificates / certificate.name)
        output.write(certificate.read_bytes())
bundle.chmod(0o644)
alias = root / "etc/ssl/cert.pem"
alias.unlink(missing_ok=True)
alias.symlink_to("certs/ca-certificates.crt")
