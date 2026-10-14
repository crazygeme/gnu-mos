import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install

cmake_install("volk", "volk-1.4.304.tar.gz", "volk-1.4.304", ("-DVOLK_INSTALL=ON",))
