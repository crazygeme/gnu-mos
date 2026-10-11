import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment, meson_install

env = environment()
build = Path(env["LFS_WORKSPACE"]) / "build/gtk3-meson"
link_flags = " ".join((
    f"-Wl,-rpath-link,{build / 'gdk'}",
    f"-Wl,-rpath-link,{build / 'gtk'}",
    env["LDFLAGS"],
))

meson_install(
    archive_source("gtk3", "gtk-3.24.49.tar.xz", "gtk-3.24.49"),
    "gtk3",
    options=(
        "-Dx11_backend=true",
        "-Dwayland_backend=false",
        "-Dintrospection=true",
        "-Dtests=false",
        "-Dinstalled_tests=false",
        "-Dexamples=false",
    ),
    env_overrides={"LDFLAGS": link_flags},
    introspection=True,
)
