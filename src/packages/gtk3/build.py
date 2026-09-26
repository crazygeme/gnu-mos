import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source('gtk3', 'gtk-3.24.49.tar.xz', 'gtk-3.24.49'),
    'gtk3',
    options=(
        '-Dx11_backend=true',
        '-Dwayland_backend=false',
        '-Dintrospection=false',
        '-Dtests=false',
        '-Dinstalled_tests=false',
        '-Dexamples=false',
    ),
)
