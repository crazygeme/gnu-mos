import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

gettext_dirs = [str(Path(__file__).with_name("gettext").resolve())]
if os.environ.get("GETTEXTDATADIRS"):
    gettext_dirs.append(os.environ["GETTEXTDATADIRS"])

source = archive_source(
    "mate-system-monitor",
    "mate-system-monitor-1.28.1.tar.xz",
    "mate-system-monitor-1.28.1",
)
subprocess.run(
    [
        "patch",
        "-p1",
        "--forward",
        "--batch",
        "-i",
        str(Path(__file__).with_name("proc-map-private-dirty.patch").resolve()),
    ],
    cwd=source,
    check=True,
)

configure_make_install(
    source,
    options=(
        "--disable-static",
        "--disable-maintainer-mode",
        "--disable-systemd",
        "--enable-wnck",
    ),
    host_tools=("glib-compile-resources", "glib-mkenums", "glib-compile-schemas"),
    env_overrides={"GETTEXTDATADIRS": ":".join(gettext_dirs)},
)
