import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("shadow", "shadow-4.18.0.tar.xz", "shadow-4.18.0"),
    options=(
        "--sysconfdir=/etc",
        "--disable-nls",
        "--disable-logind",
        "--disable-subordinate-ids",
        "--without-libpam",
        "--without-audit",
        "--without-btrfs",
        "--without-selinux",
        "--without-acl",
        "--without-attr",
        "--without-tcb",
        "--without-nscd",
        "--without-sssd",
        "--with-libbsd",
    ),
)
