import json
import os
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment, meson_install

build_libdir = Path(os.environ["LFS_WORKSPACE"]) / "build/pango-meson/pango"
link_args = shlex.split(environment()["LDFLAGS"])
link_args.insert(0, f"-Wl,-rpath-link,{build_libdir}")

meson_install(
    archive_source("pango", "pango-1.56.3.tar.xz", "pango-1.56.3"),
    "pango",
    options=(
        "-Dintrospection=disabled",
        "-Dbuild-testsuite=false",
        "-Dbuild-examples=false",
        "-Dc_link_args=" + json.dumps(link_args),
    ),
)
