import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source('cairo', 'cairo-1.18.4.tar.xz', 'cairo-1.18.4'),
    'cairo',
    options=(
        '-Dtests=disabled',
    ),
)
