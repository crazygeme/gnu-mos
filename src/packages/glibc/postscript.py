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

# Use the target loader and localedef to match the installed libc and ABI.
subprocess.run(
    [
        str(sysroot / "usr/lib/ld-linux.so.2"),
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
