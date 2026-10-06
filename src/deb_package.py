"""Extract a configured Debian binary package into the target sysroot."""

import json
import os
from pathlib import Path
import shutil
import subprocess


def install_deb() -> None:
    directory = Path(os.environ["LFS_PACKAGE_DIR"])
    info = json.loads((directory / "package.json").read_text())
    archive = Path(os.environ["LFS_SOURCES"]) / info["archive"]
    arch = os.environ["LFS_ARCH"]
    if arch not in info.get("architectures", ("x86", "x64")):
        raise ValueError(f"package {info['name']} does not support {arch}")
    dpkg_deb = shutil.which("dpkg-deb", path="/usr/bin:/bin")
    if dpkg_deb is None:
        raise RuntimeError("Debian binary extraction requires the host dpkg-deb utility")
    result = subprocess.run(
        [dpkg_deb, "--field", str(archive), "Package", "Version", "Architecture"],
        capture_output=True,
        text=True,
        check=True,
    )
    fields = dict(line.split(": ", 1) for line in result.stdout.splitlines())
    expected_package = info.get("deb-package", info["name"])
    if fields.get("Package") != expected_package:
        raise ValueError(f"unexpected Debian package identity for {info['name']}")
    if fields.get("Version") != info["version"]:
        raise ValueError(f"unexpected Debian package version for {info['name']}")
    expected_arch = {"x86": "i386", "x64": "amd64"}[arch]
    if fields.get("Architecture") not in (expected_arch, "all"):
        raise ValueError(f"Debian package architecture does not match {arch}")
    sysroot = Path(os.environ["LFS_SYSROOT"])
    sysroot.mkdir(parents=True, exist_ok=True)
    tar = shutil.which("tar", path="/usr/bin:/bin")
    if tar is None:
        raise RuntimeError("Debian binary extraction requires the host GNU tar utility")
    command = [dpkg_deb, "--fsys-tarfile", str(archive)]
    # Retain directory aliases such as bin -> usr/bin during payload extraction.
    with subprocess.Popen(command, stdout=subprocess.PIPE) as payload:
        try:
            subprocess.run(
                [
                    tar,
                    "--extract",
                    "--preserve-permissions",
                    "--no-same-owner",
                    "--keep-directory-symlink",
                    "--file=-",
                    "--directory=" + str(sysroot),
                ],
                stdin=payload.stdout,
                check=True,
            )
        finally:
            payload.stdout.close()
        result = payload.wait()
        if result:
            raise subprocess.CalledProcessError(result, command)


if __name__ == "__main__":
    install_deb()
