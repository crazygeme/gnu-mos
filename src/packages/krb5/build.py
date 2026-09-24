import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

source = archive_source("krb5", "krb5-1.22.1.tar.gz", "krb5-1.22.1")
configure_make_install(
    source / "src",
    options=("--enable-shared", "--disable-static"),
    env_overrides={
        "krb5_cv_attr_constructor_destructor": "yes,yes",
        "ac_cv_printf_positional": "yes",
    },
)
