import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install
meson_install(archive_source("mutter", "mutter-48.4.tar.xz", "mutter-48.4"), "mutter", ("-Dnative_tests=false", "-Dtests=false", "-Dwayland=false", "-Dxwayland=false", "-Dnative_backend=false"))
