import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("libgtop", "libgtop-2.40.0.tar.xz", "libgtop-2.40.0")
subprocess.run(
    [
        "patch", "-p1", "--forward", "--batch", "-i",
        str(Path(__file__).with_name("daemon-proc-io-pid.patch").resolve()),
    ],
    cwd=source,
    check=True,
)

configure_make_install(
    source,
    options=(
        "--disable-static",
        "--disable-introspection",
        "--disable-gtk-doc",
    ),
    env_overrides={"CFLAGS": "-O2 -m32 -std=gnu11"},
)
