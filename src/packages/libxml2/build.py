import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source("libxml2", "libxml2-2.13.8.tar.xz", "libxml2-2.13.8")
subprocess.run(
    [
        "patch",
        "-p1",
        "--forward",
        "--batch",
        "-i",
        str(Path(__file__).with_name("meson-icu-uc.patch")),
    ],
    cwd=source,
    check=True,
)
workspace = Path(os.environ["LFS_WORKSPACE"])
tools = workspace / "tools"
host_build = workspace / "build/libxml2-host-meson"
subprocess.run(
    [
        "meson",
        "setup",
        str(host_build),
        str(source),
        "--prefix=" + str(tools),
        "--libdir=lib",
        "-Dpython=false",
        "-Dicu=enabled",
    ],
    check=True,
)
subprocess.run(["meson", "compile", "-C", str(host_build)], check=True)
subprocess.run(["meson", "install", "-C", str(host_build)], check=True)
meson_install(source, "libxml2", ("--libdir=lib", "-Dpython=false", "-Dicu=enabled"))

for pkgconfig in (
    tools / "lib/pkgconfig/libxml-2.0.pc",
    Path(os.environ["LFS_SYSROOT"]) / "usr/lib/pkgconfig/libxml-2.0.pc",
):
    contents = pkgconfig.read_text(encoding="utf-8")
    old = "Cflags: -I${includedir}\n"
    if contents.count(old) != 1:
        raise RuntimeError(f"unexpected libxml2 pkg-config flags: {pkgconfig}")
    pkgconfig.write_text(
        contents.replace(old, "Cflags: -I${includedir}/libxml2\n"),
        encoding="utf-8",
    )
