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
    env["CFLAGS"] = "-O2 -m32"
    env["LDFLAGS"] = "--sysroot=" + str(sysroot) + " -Wl,-rpath-link," + str(sysroot / "usr/lib")
    env["LD_LIBRARY_PATH"] = ":".join((str(sysroot / "usr/lib"), str(sysroot / "lib")))
    env["PKG_CONFIG_SYSROOT_DIR"] = str(sysroot)
    env["PKG_CONFIG_LIBDIR"] = ":".join((
        str(sysroot / "usr/lib/pkgconfig"),
        str(sysroot / "usr/share/pkgconfig"),
    ))
    env.pop("PKG_CONFIG_PATH", None)
    return env

def archive_source(name, archive, directory, excluded_members=()):
    sources = Path(os.environ["LFS_SOURCES"]); build = Path(os.environ["LFS_WORKSPACE"]) / "build"
    target = build / directory
    if target.exists():
        import shutil
        shutil.rmtree(target)
    def extraction_filter(member, destination):
        if member.name in excluded_members:
            return None
        return tarfile.data_filter(member, destination)

    with tarfile.open(sources / archive) as package:
        package.extractall(build, filter=extraction_filter)
    return target

def configure_make_install(source, prefix="/usr", options=(), env_overrides=None):
    env = environment()
    if env_overrides:
        env.update(env_overrides)
    target = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
    subprocess.run([
        str(source / "configure"),
        "--build=x86_64-pc-linux-gnu",
        "--host=" + target,
        "--prefix=" + prefix,
        *options,
    ], cwd=source, env=env, check=True)
    subprocess.run(["make", "-j" + str(os.cpu_count() or 1)], cwd=source, env=env, check=True)
    subprocess.run(["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], "install"], cwd=source, env=env, check=True)
    # Libtool archives record build-time absolute paths and are not needed by
    # consumers once shared libraries and pkg-config metadata are installed.
    for archive in Path(os.environ["LFS_SYSROOT"]).rglob("*.la"):
        archive.unlink()

def meson_install(source, name, options=()):
    build = Path(os.environ["LFS_WORKSPACE"]) / "build" / (name + "-meson")
    build.mkdir(parents=True, exist_ok=True)
    env = environment()
    target = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
    cross = build / "cross-file.ini"
    cross.write_text(
        "[binaries]\n"
        f"c = '{target}-gcc'\n"
        f"cpp = '{target}-g++'\n"
        f"ar = '{target}-ar'\n"
        f"strip = '{target}-strip'\n"
        "pkg-config = 'pkg-config'\n"
        "\n[host_machine]\n"
        "system = 'linux'\n"
        "cpu_family = 'x86'\n"
        "cpu = 'i686'\n"
        "endian = 'little'\n"
        "\n[properties]\n"
        "needs_exe_wrapper = true\n",
        encoding="ascii",
    )
    subprocess.run(["meson", "setup", str(build), str(source), "--cross-file", str(cross), "--prefix=/usr", *options], env=env, check=True)
    subprocess.run(["meson", "compile", "-C", str(build)], env=env, check=True)
    subprocess.run(["meson", "install", "-C", str(build), "--destdir", os.environ["LFS_SYSROOT"]], env=env, check=True)
