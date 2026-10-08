import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source('diffutils', 'diffutils-3.12.tar.xz', 'diffutils-3.12'),
    env_overrides={
        'gl_cv_func_strcasecmp_works': 'yes',
    },
)
