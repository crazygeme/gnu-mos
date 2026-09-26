import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

source = archive_source("hwdata", "hwdata-0.394.tar.gz", "hwdata-0.394")
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
for prefix in (Path(os.environ["LFS_SYSROOT"]) / "usr", tools):
    data = prefix / "share/hwdata"
    data.mkdir(parents=True, exist_ok=True)
    for name in ("pnp.ids", "pci.ids", "usb.ids"):
        shutil.copy2(source / name, data / name)

# Native code generators require a host-readable hardware database path.
pkgconfig = tools / "lib/pkgconfig"
pkgconfig.mkdir(parents=True, exist_ok=True)
(pkgconfig / "hwdata.pc").write_text(
    f"prefix={tools}\npkgdatadir=${{prefix}}/share/hwdata\n"
    "Name: hwdata\nDescription: Hardware identification databases\nVersion: 0.394\n"
)
