import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install

sysroot = os.environ["LFS_SYSROOT"]
cmake_install(
    'spirv-tools', 'spirv-tools-vulkan-sdk-1.4.309.0.tar.gz', 'SPIRV-Tools-vulkan-sdk-1.4.309.0',
    options=(
        '-DSPIRV_SKIP_TESTS=ON',
        '-DSPIRV_SKIP_EXECUTABLES=ON',
        f'-DSPIRV-Headers_SOURCE_DIR={sysroot}/usr',
    ),
)
