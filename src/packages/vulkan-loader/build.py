import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install

cmake_install(
    'vulkan-loader', 'vulkan-loader-v1.4.309.tar.gz', 'Vulkan-Loader-1.4.309',
    options=(
        '-DBUILD_WSI_WAYLAND_SUPPORT=OFF',
    ),
)
