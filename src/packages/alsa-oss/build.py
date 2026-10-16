"""Build ALSA playback and mixer plugins for the OSS device interface."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install
configure_make_install(
    archive_source("alsa-oss", "alsa-plugins-1.2.12.tar.bz2", "alsa-plugins-1.2.12"),
    options=("--enable-oss", "--with-alsalconfdir=/etc/alsa/conf.d"),
    make_options=("-C", "oss"),
)
