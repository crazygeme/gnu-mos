import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[2]))
from package_lib import archive_source,configure_make_install
configure_make_install(
    archive_source("git", "git-2.51.0.tar.xz", "git-2.51.0"),
    options=("--with-curl", "--with-expat"),
    # The target iconv implementation emits the UTF-16/UTF-32 BOM.  Git's
    # configure test executes a target binary, which is unavailable during
    # this cross build, so provide the target property explicitly.
    env_overrides={
        "ac_cv_iconv_omits_bom": "no",
        # These checks execute target binaries and therefore cannot run in
        # the cross build.  Linux/glibc has the normal behaviours.
        "ac_cv_fread_reads_directories": "yes",
        "ac_cv_snprintf_returns_bogus": "no",
    },
)
