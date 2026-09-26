import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, meson_install

meson_install(
    archive_source('libwnck', 'libwnck-43.2.tar.xz', 'libwnck-43.2'),
    'libwnck',
    options=(
        '-Dintrospection=disabled',
        '-Dgtk_doc=false',
    ),
)
