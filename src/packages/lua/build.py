import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("lua", "lua-5.4.8.tar.gz", "lua-5.4.8")
env = environment()
subprocess.run(
    ["make", "-j4", "linux", "CC=" + env["CC"], "AR=" + env["AR"] + " rcu",
     "RANLIB=" + env["RANLIB"], "MYCFLAGS=" + env["CFLAGS"] + " -fPIC -std=gnu17",
     "MYLDFLAGS=" + env["LDFLAGS"]],
    cwd=source, env=env, check=True,
)
subprocess.run(
    ["make", "install", "INSTALL_TOP=" + str(Path(env["LFS_SYSROOT"]) / "usr")],
    cwd=source, env=env, check=True,
)
metadata = Path(env["LFS_SYSROOT"]) / "usr/lib/pkgconfig/lua.pc"
metadata.parent.mkdir(parents=True, exist_ok=True)
metadata.write_text(
    "prefix=/usr\nlibdir=${prefix}/lib\nincludedir=${prefix}/include\n\n"
    "Name: Lua\nDescription: Lua language library\nVersion: 5.4.8\n"
    "Libs: -L${libdir} -llua -lm -ldl\nCflags: -I${includedir}\n"
)
