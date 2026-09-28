import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("librsvg", "librsvg-2.40.21.tar.xz", "librsvg-2.40.21")
subprocess.run(
    [
        "patch",
        "-p1",
        "--forward",
        "--batch",
        "-i",
        str(Path(__file__).with_name("libxml2-const-errors.patch").resolve()),
    ],
    cwd=source,
    check=True,
)

configure_make_install(
    source,
    options=(
        "--disable-static",
        "--disable-introspection",
        "--disable-vala",
        "--disable-gtk-doc",
        "--disable-pixbuf-loader",
    ),
    env_overrides={"CFLAGS": "-O2 -m32 -std=gnu11"},
)
