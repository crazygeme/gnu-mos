import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("xterm", "xterm-411.tgz", "xterm-411"),
    options=(
        "--disable-setuid",
        "--disable-setgid",
        "--enable-wide-chars",
        "--enable-freetype",
        "--with-tty-group=tty",
        "--with-app-defaults=/usr/share/X11/app-defaults",
        "--with-terminal-type=xterm-256color",
    ),
)
