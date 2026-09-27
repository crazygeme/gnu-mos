import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(archive_source("sed", "sed-4.9.tar.xz", "sed-4.9"))
