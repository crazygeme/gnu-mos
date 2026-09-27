import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, configure_make_install

configure_make_install(
    archive_source("mate-calc", "mate-calc-1.28.0.tar.xz", "mate-calc-1.28.0"),
    options=(
        "--disable-maintainer-mode",
    ),
    host_tools=("glib-compile-resources", "glib-mkenums", "glib-compile-schemas"),
    # Static dependencies must follow MPC in the final linker arguments.
    env_overrides={"LIBS": "-lmpc -lmpfr -lgmp -lm"},
)
