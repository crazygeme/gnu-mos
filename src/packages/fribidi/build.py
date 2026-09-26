import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source('fribidi', 'fribidi-1.0.16.tar.xz', 'fribidi-1.0.16'),
    'fribidi',
    options=(
        '-Ddocs=false',
        '-Dtests=false',
    ),
)
