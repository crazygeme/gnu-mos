import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source(
    "shared-mime-info", "shared-mime-info-2.4.tar.gz", "shared-mime-info-2.4"
)
workspace = Path(os.environ["LFS_WORKSPACE"])
host_build = workspace / "build/shared-mime-info-host-meson"
host_env = os.environ.copy()
host_env["PKG_CONFIG_PATH"] = str(workspace / "tools/lib/pkgconfig")
subprocess.run(
    [
        "meson", "setup", str(host_build), str(source),
        "--prefix=" + str(workspace / "tools"),
        "-Dbuild-tests=false", "-Dbuild-translations=false",
    ],
    env=host_env,
    check=True,
)
subprocess.run(["meson", "compile", "-C", str(host_build)], env=host_env, check=True)
meson_install(
    source, "shared-mime-info",
    ("-Dbuild-tests=false", "-Dbuild-translations=false"),
)
subprocess.run(
    [str(host_build / "src/update-mime-database"), str(Path(os.environ["LFS_SYSROOT"]) / "usr/share/mime")],
    check=True,
)
