import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("which", "which-2.21.tar.gz", "which-2.21")
configure_make_install(source)
