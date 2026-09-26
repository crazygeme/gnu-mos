import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("libevent", "libevent-2.1.12-stable.tar.gz", "libevent-2.1.12-stable"),
    options=("--disable-samples", "--disable-libevent-regress"),
    env_overrides={"ac_cv_func_epoll_ctl": "no", "ac_cv_header_sys_epoll_h": "no"},
)
