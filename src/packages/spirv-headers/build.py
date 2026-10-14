import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install

cmake_install(
    'spirv-headers', 'spirv-headers-vulkan-sdk-1.4.309.0.tar.gz', 'SPIRV-Headers-vulkan-sdk-1.4.309.0',
    options=(
    ),
)
