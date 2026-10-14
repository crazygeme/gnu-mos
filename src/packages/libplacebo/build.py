import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

source = archive_source("libplacebo", "libplacebo-v7.349.0.tar.gz", "libplacebo-7.349.0")
for patch_name in ("python-elementtree.patch", "glslang-library.patch", "ffmpeg-version-header.patch"):
    patch = Path(__file__).with_name(patch_name)
    for options in (("--dry-run",), ()):
        subprocess.run(
            ["patch", "--batch", "-p1", *options, "-i", str(patch)],
            cwd=source, check=True,
        )
meson_install(
    source, "libplacebo",
    options=(
        "--libdir=lib", "-Dvulkan=enabled", "-Dglslang=enabled",
        "-Dshaderc=disabled", "-Dopengl=enabled", "-Dtests=false", "-Ddemos=false",
        "-Dvulkan-registry=" + os.environ["LFS_SYSROOT"] + "/usr/share/vulkan/registry/vk.xml",
    ),
    host_tools=(),
)
