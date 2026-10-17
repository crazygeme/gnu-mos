"""Build PCI inventory, configuration, and access library utilities."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("pciutils", "pciutils-3.15.0.tar.xz", "pciutils-3.15.0")
env = environment()
options = [
    "PREFIX=/usr",
    "SBINDIR=/usr/sbin",
    "LSPCIDIR=/usr/bin",
    "IDSDIR=/usr/share/hwdata",
    "HOST=" + ("x86_64-linux" if env["LFS_BITS"] == "64" else "i386-linux"),
    "CROSS_COMPILE=" + env["LFS_TARGET"] + "-",
    "SHARED=yes",
    "ZLIB=yes",
    "HWDB=yes",
    "OPT=" + env["CFLAGS"],
    "LDFLAGS=" + env["LDFLAGS"],
]
subprocess.run(["make", "-j4", *options], cwd=source, env=env, check=True)
subprocess.run(
    ["make", *options, "DESTDIR=" + env["LFS_SYSROOT"], "install", "install-lib"],
    cwd=source, env=env, check=True,
)
