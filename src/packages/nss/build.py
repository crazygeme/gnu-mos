import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source, environment

source = archive_source("nss", "nss-3.123.tar.gz", "nss-3.123") / "nss"
env = environment()
root = Path(env["LFS_SYSROOT"])
dist = Path(env["LFS_WORKSPACE"]) / "build/nss-dist"
common = [
    "BUILD_OPT=1",
    "OBJDIR_NAME=lfs.OBJ",
    "SOURCE_PREFIX=" + str(dist),
    "NSDISTMODE=copy",
]

# Build nsinstall with the native ABI before target headers enter the build.
native = os.environ.copy()
native.update(PATH="/usr/bin:/bin", CFLAGS="", CXXFLAGS="", LDFLAGS="")
subprocess.run(
    [
        "make", "-C", str(source / "coreconf/nsinstall"), "program", *common,
        "CC=/usr/bin/gcc", "CCC=/usr/bin/g++", "LD=/usr/bin/ld",
        "AR=/usr/bin/ar cr $@", "RANLIB=/usr/bin/ranlib", "USE_64=1",
    ],
    env=native, check=True,
)
subprocess.run(
    [
        "make", "-j4", "all", *common,
        "CC=" + env["CC"] + " --sysroot=" + str(root),
        "CCC=" + env["CXX"] + " --sysroot=" + str(root),
        "LD=" + env["LD"], "AR=" + env["AR"] + " cr $@",
        "RANLIB=" + env["RANLIB"],
        "NSINSTALL=" + str(source / "coreconf/nsinstall/lfs.OBJ/nsinstall"),
        "CROSS_COMPILE=1", "NSS_DISABLE_GTESTS=1",
        "NSPR_INCLUDE_DIR=" + str(root / "usr/include/nspr"),
        "NSPR_LIB_DIR=" + str(root / "usr/lib"),
        "NSS_USE_SYSTEM_SQLITE=1",
        "SQLITE_INCLUDE_DIR=" + str(root / "usr/include"),
        "SQLITE_LIB_DIR=" + str(root / "usr/lib"),
        # Command-line OS_LIBS suppresses makefile additions, including zlib.
        # Both static-library dependencies follow their consuming objects.
        "OS_LIBS=$(OS_PTHREAD) -ldl -lc -lm $(ZLIB_LIBS)",
        "USE_SYSTEM_ZLIB=1",
        *(["USE_64=1"] if env["LFS_ARCH"] == "x64" else []),
    ],
    cwd=source, env=env, check=True,
)
library_dir = root / "usr/lib"
binary_dir = root / "usr/bin"
include_dir = root / "usr/include/nss"
for directory in (library_dir, binary_dir, include_dir, library_dir / "pkgconfig"):
    directory.mkdir(parents=True, exist_ok=True)
for pattern in ("*.so", "*.a", "*.chk"):
    for library in (dist / "lfs.OBJ/lib").glob(pattern):
        shutil.copy2(library, library_dir / library.name)
for executable in (dist / "lfs.OBJ/bin").iterdir():
    if executable.is_file():
        shutil.copy2(executable, binary_dir / executable.name)
shutil.copytree(dist / "public/nss", include_dir, dirs_exist_ok=True)
(library_dir / "pkgconfig/nss.pc").write_text(
    "prefix=/usr\nexec_prefix=${prefix}\nlibdir=${prefix}/lib\n"
    "includedir=${prefix}/include/nss\n\n"
    "Name: NSS\nDescription: Network Security Services\nVersion: 3.123\n"
    "Requires: nspr >= 4.38.2\n"
    "Libs: -L${libdir} -lnss3 -lsmime3 -lssl3 -lnssutil3\n"
    "Cflags: -I${includedir}\n"
)
