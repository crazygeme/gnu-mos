import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("mesa-utils", "mesa-demos-9.0.0.tar.xz", "mesa-demos-9.0.0")
env = environment()
target = Path(os.environ["LFS_SYSROOT"]) / "usr/bin"
target.mkdir(parents=True, exist_ok=True)
common = [source / "src/util/glinfo_common.c", source / "src/glad/src/glad.c"]
# The diagnostic targets consume the upstream sources without source changes.
programs = {
    "glxinfo": ([source / "src/xdemos/glxinfo.c", *common], ["gl", "x11"]),
    "glxgears": ([source / "src/xdemos/glxgears.c"], ["gl", "x11"]),
    "eglinfo": ([source / "src/egl/opengl/eglinfo.c", *common], ["egl", "gl"]),
}
for name, (files, dependencies) in programs.items():
    flags = shlex.split(subprocess.check_output(
        ["pkg-config", "--cflags", "--libs", *dependencies], env=env, text=True
    ))
    subprocess.run(
        [env["CC"], *shlex.split(env["CFLAGS"]), "-D_GNU_SOURCE", "-std=c11",
         "-I" + str(source / "src/util"), "-I" + str(source / "src/glad/include"),
         *(str(path) for path in files), *shlex.split(env["LDFLAGS"]),
         *flags, "-lm", "-ldl", "-o", str(target / name)],
        env=env, check=True,
    )
