import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install
configure_make_install(archive_source("ncurses", "ncurses-6.5.tar.gz", "ncurses-6.5"), options=("--with-shared", "--without-debug", "--without-ada", "--enable-widec"))
