import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source(
        "startup-notification",
        "startup-notification-0.12.tar.gz",
        "startup-notification-0.12",
    ),
    env_overrides={"lf_cv_sane_realloc": "yes"},
    options=("--disable-static",),
)
