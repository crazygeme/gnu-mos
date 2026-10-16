import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import cmake_install
cmake_install('portaudio', 'portaudio-19.7.0.tar.gz', 'portaudio-19.7.0', options=("-DPA_USE_ALSA=ON", "-DPA_BUILD_SHARED=ON", "-DPA_BUILD_STATIC=OFF", "-DPA_BUILD_EXAMPLES=OFF", "-DPA_BUILD_TESTS=OFF"))
