import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install

cmake_install(
    'vulkan-headers', 'vulkan-headers-v1.4.309.tar.gz', 'Vulkan-Headers-1.4.309',
    options=(
    ),
)
