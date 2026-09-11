import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[2]))
from package_lib import archive_source,configure_make_install
configure_make_install(archive_source("perl","perl-5.42.0.tar.xz","perl-5.42.0"), options=("-Duseshrplib",))
