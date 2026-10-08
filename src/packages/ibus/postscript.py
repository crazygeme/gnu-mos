import os
import subprocess
from pathlib import Path

sysroot = Path(os.environ["LFS_SYSROOT"]).resolve()
loader_name = "ld-linux-x86-64.so.2" if os.environ["LFS_ARCH"] == "x64" else "ld-linux.so.2"
command = [
    str(sysroot / "usr/lib" / loader_name),
    "--library-path", f"{sysroot / 'usr/lib'}:{sysroot / 'lib'}",
]
subprocess.run(
    [*command, str(sysroot / "usr/bin/glib-compile-schemas"),
     str(sysroot / "usr/share/glib-2.0/schemas")],
    check=True,
)
subprocess.run(
    [*command, str(sysroot / "usr/bin/dconf"), "update", str(sysroot / "etc/dconf/db")],
    check=True,
)
modules = sysroot / "usr/lib/gtk-3.0/3.0.0/immodules"
result = subprocess.run(
    [*command, str(sysroot / "usr/bin/gtk-query-immodules-3.0"),
     *(str(module) for module in sorted(modules.glob("*.so")))],
    check=True, capture_output=True, text=True,
)
(modules.parent / "immodules.cache").write_text(result.stdout.replace(str(sysroot), ""))
