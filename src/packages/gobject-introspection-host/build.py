import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source

workspace = Path(os.environ["LFS_WORKSPACE"])
sysroot = Path(os.environ["LFS_SYSROOT"])
tools = workspace / "tools"
source = archive_source(
    "gobject-introspection-host", "gobject-introspection-1.84.0.tar.xz", "gobject-introspection-1.84.0"
)
build = workspace / "build/gobject-introspection-host"
env = os.environ.copy()
for variable in (
    "CC", "CXX", "AR", "AS", "LD", "RANLIB", "STRIP", "NM", "CFLAGS", "CXXFLAGS",
    "CPPFLAGS", "LDFLAGS", "LD_LIBRARY_PATH", "LIBRARY_PATH", "CPATH", "PKG_CONFIG",
    "PKG_CONFIG_PATH", "PKG_CONFIG_LIBDIR", "PKG_CONFIG_SYSROOT_DIR", "PYTHONPATH", "DESTDIR",
):
    env.pop(variable, None)
env.update(PATH=f"{tools / 'bin'}:/usr/bin:/bin", CC="gcc", CXX="g++", CFLAGS="-O2")
subprocess.run(
    ["meson", "setup", str(build), str(source), "--prefix=" + str(tools), "--libdir=lib",
     "--wrap-mode=nofallback", "-Dpython=" + str(tools / "bin/python3.13"), "-Dtests=false",
     "-Dbuild_introspection_data=false"],
    env=env, check=True,
)
subprocess.run(["meson", "compile", "-C", str(build)], env=env, check=True)
subprocess.run(["meson", "install", "-C", str(build)], env=env, check=True)

loader_name = "ld-linux-x86-64.so.2" if os.environ["LFS_ARCH"] == "x64" else "ld-linux.so.2"
loader = shlex.quote(str(sysroot / "usr/lib" / loader_name))
library_path = shlex.quote(f"{sysroot / 'usr/lib'}:{sysroot / 'lib'}")
bin_dir = tools / "bin"
for name, operation in (("lfs-run-target", ""), ("lfs-ldd-target", "--list ")):
    script = bin_dir / name
    script.write_text(
        "#!/bin/sh\n"
        f"libraries={library_path}\n"
        'if [ -n "${GI_LIBRARY_PATH:-}" ]; then libraries="$GI_LIBRARY_PATH:$libraries"; fi\n'
        f'exec {loader} --library-path "$libraries" {operation}"$@"\n'
    )
    script.chmod(0o755)

(sysroot / "usr/share/gir-1.0").mkdir(parents=True, exist_ok=True)
scanner = bin_dir / "g-ir-scanner-cross"
scanner.write_text(
    "#!/bin/sh\n"
    f"export LD_LIBRARY_PATH={shlex.quote(str(tools / 'lib'))}\n"
    f"exec {shlex.quote(str(bin_dir / 'g-ir-scanner'))} "
    f"--use-binary-wrapper={shlex.quote(str(bin_dir / 'lfs-run-target'))} "
    f"--use-ldd-wrapper={shlex.quote(str(bin_dir / 'lfs-ldd-target'))} "
    "--lib-dirs-envvar=GI_LIBRARY_PATH --no-libtool "
    f"--add-include-path={shlex.quote(str(sysroot / 'usr/share/gir-1.0'))} \"$@\"\n"
)
scanner.chmod(0o755)
compiler = bin_dir / "g-ir-compiler-cross"
compiler.write_text(
    "#!/bin/sh\n"
    f"export LD_LIBRARY_PATH={shlex.quote(str(tools / 'lib'))}\n"
    f"exec {shlex.quote(str(bin_dir / 'g-ir-compiler'))} "
    f"--includedir={shlex.quote(str(sysroot / 'usr/share/gir-1.0'))} \"$@\"\n"
)
compiler.chmod(0o755)
