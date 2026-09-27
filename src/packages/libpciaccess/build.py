import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source("libpciaccess", "libpciaccess-0.18.1.tar.xz", "libpciaccess-0.18.1")
subprocess.run(
    ["patch", "-p1", "--forward", "--batch", "-i",
     str(Path(__file__).with_name("rom-read-progress.patch").resolve())],
    cwd=source,
    check=True,
)

meson_install(
    source,
    "libpciaccess",
    options=("-Dzlib=enabled", "-Dlinux-rom-fallback=true"),
    host_tools=(),
)
