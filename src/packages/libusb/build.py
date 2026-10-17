"""Build the USB access library with udev discovery."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("libusb", "libusb-1.0.29.tar.bz2", "libusb-1.0.29")
subprocess.run(
    ["patch", "-p1", "--forward", "--batch", "-i",
     str(Path(__file__).with_name("mos-usbfs-version.patch"))],
    cwd=source, check=True,
)
configure_make_install(source, options=("--disable-static", "--enable-udev"))
