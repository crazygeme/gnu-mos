import os, subprocess, tarfile
from pathlib import Path

def environment():
    env = os.environ.copy()
    target = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
    sysroot = Path(env["LFS_SYSROOT"])
    env["CC"] = target + "-gcc"
    env["CXX"] = target + "-g++"
    env["AR"] = target + "-ar"
    env["AS"] = target + "-as"
    env["LD"] = target + "-ld"
    env["RANLIB"] = target + "-ranlib"
    env["STRIP"] = target + "-strip"
    env["NM"] = target + "-nm"
    env["CFLAGS"] = "-m32"
    env["PKG_CONFIG_SYSROOT_DIR"] = str(sysroot)
    env["PKG_CONFIG_LIBDIR"] = ":".join((
        str(sysroot / "usr/lib/pkgconfig"),
        str(sysroot / "usr/share/pkgconfig"),
    ))
    env.pop("PKG_CONFIG_PATH", None)
    return env

def archive_source(name, archive, directory):
    sources = Path(os.environ["LFS_SOURCES"]); build = Path(os.environ["LFS_WORKSPACE"]) / "build"
    target = build / directory
    if target.exists():
        import shutil
        shutil.rmtree(target)
    with tarfile.open(sources / archive) as package: package.extractall(build, filter="data")
    return target

def configure_make_install(source, prefix="/usr", options=()):
    env = environment(); subprocess.run([str(source / "configure"), "--prefix=" + prefix, *options], cwd=source, env=env, check=True)
    subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=source, env=env, check=True)
    subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=source, env=env, check=True)

def meson_install(source, name, options=()):
    build = Path(os.environ["LFS_WORKSPACE"]) / "build" / (name + "-meson")
    build.mkdir(parents=True, exist_ok=True)
    env = environment()
    subprocess.run(["meson", "setup", str(build), str(source), "--prefix=/usr", *options], env=env, check=True)
    subprocess.run(["meson", "compile", "-C", str(build)], env=env, check=True)
    subprocess.run(["meson", "install", "-C", str(build), "--destdir", os.environ["LFS_SYSROOT"]], env=env, check=True)
