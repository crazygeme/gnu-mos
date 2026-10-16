import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import environment

env = environment()
package = Path(__file__).parent
output = Path(env["LFS_SYSROOT"]) / 'usr/lib/gio/modules/libgiomosvolume.so'
output.parent.mkdir(parents=True, exist_ok=True)
flags = subprocess.check_output(
    ["pkg-config", "--cflags", "--libs", *'gio-2.0 gmodule-2.0'.split()], env=env, text=True
)
subprocess.run(
    [env["CC"], *shlex.split(env["CFLAGS"]), "-Wall", "-Werror",
     *['-shared', '-fPIC'], str(package / 'monitor.c'), "-o", str(output),
     *shlex.split(env["LDFLAGS"]), *shlex.split(flags)],
    env=env, check=True,
)
