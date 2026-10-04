import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"]).resolve()
i18n = sysroot / "usr/share/i18n"
locale = sysroot / "usr/lib/locale/C.utf8"
locale.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["I18NPATH"] = str(i18n)
env["LC_ALL"] = "C"

loader = (
    "ld-linux-x86-64.so.2" if os.environ.get("LFS_ARCH") == "x64" else "ld-linux.so.2"
)

# Use the target loader and localedef to match the installed libc and ABI.
subprocess.run(
    [
        str(sysroot / "usr/lib" / loader),
        "--library-path",
        str(sysroot / "usr/lib") + ":" + str(sysroot / "lib"),
        str(sysroot / "usr/bin/localedef"),
        "--no-archive",
        "--little-endian",
        "-i",
        str(i18n / "locales/C"),
        "-f",
        # Named charmaps use I18NPATH and support compressed source files.
        "UTF-8",
        str(locale),
    ],
    env=env,
    check=True,
)
