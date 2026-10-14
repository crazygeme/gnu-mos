import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install

cmake_install(
    'glslang', 'glslang-15.1.0.tar.gz', 'glslang-15.1.0',
    options=(
        '-DALLOW_EXTERNAL_SPIRV_TOOLS=ON',
        '-DENABLE_GLSLANG_BINARIES=OFF',
        '-DGLSLANG_TESTS=OFF',
        '-DENABLE_OPT=ON',
    ),
)
