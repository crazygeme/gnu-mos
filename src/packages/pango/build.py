import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source('pango', 'pango-1.56.3.tar.xz', 'pango-1.56.3'),
    'pango',
    options=(
        '-Dintrospection=disabled',
        '-Dbuild-testsuite=false',
        '-Dbuild-examples=false',
    ),
)
