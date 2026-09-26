import os, shutil, subprocess, tarfile
from pathlib import Path


GLIB_HOST_TOOLS = (
    "glib-compile-resources",
    "glib-compile-schemas",
    "glib-genmarshal",
    "glib-mkenums",
    "gdbus-codegen",
)


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
    tools = Path(env["LFS_WORKSPACE"]) / "tools"
    env["PATH"] = ":".join(
        (str(tools / "bin"), "/usr/bin", "/bin", env.get("PATH", ""))
    )
    env["CFLAGS"] = "-O2 -m32"
    env["CXXFLAGS"] = "-O2 -m32"
    env["LDFLAGS"] = (
        "--sysroot=" + str(sysroot) + " -Wl,-rpath-link," + str(sysroot / "usr/lib")
    )
    # Build-time executables load host libraries from the tools prefix.
    env["LD_LIBRARY_PATH"] = str(tools / "lib")
    env["PKG_CONFIG_SYSROOT_DIR"] = str(sysroot)
    env["PKG_CONFIG_LIBDIR"] = ":".join(
        (
            str(sysroot / "usr/lib/pkgconfig"),
            str(sysroot / "usr/share/pkgconfig"),
        )
    )
    env.pop("PKG_CONFIG_PATH", None)
    return env


def archive_source(name, archive, directory, excluded_members=()):
    sources = Path(os.environ["LFS_SOURCES"])
    build = Path(os.environ["LFS_WORKSPACE"]) / "build"
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


def host_tool_paths(env, names):
    host_path = ":".join((str(Path(env["LFS_WORKSPACE"]) / "tools/bin"), "/usr/bin", "/bin"))
    result = {}
    for name in names:
        executable = shutil.which(name, path=host_path)
        if executable is None:
            raise RuntimeError(f"required host tool not found: {name}")
        result[name] = executable
    return result


def configure_make_install(source, prefix="/usr", options=(), env_overrides=None, host_tools=()):
    env = environment()
    tool_variables = {
        name.upper().replace("-", "_"): path
        for name, path in host_tool_paths(env, host_tools).items()
    }
    env.update(tool_variables)
    if env_overrides:
        env.update(env_overrides)
    make_tools = [f"{name}={env[name]}" for name in tool_variables]
    target = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
    subprocess.run(
        [
            str(source / "configure"),
            "--build=x86_64-pc-linux-gnu",
            "--host=" + target,
            "--prefix=" + prefix,
            *options,
        ],
        cwd=source,
        env=env,
        check=True,
    )
    subprocess.run(["make", "-j4", *make_tools], cwd=source, env=env, check=True)
    subprocess.run(
        ["make", "DESTDIR=" + os.environ["LFS_SYSROOT"], *make_tools, "install"],
        cwd=source,
        env=env,
        check=True,
    )
    # Libtool archives record build-time absolute paths and are not needed by
    # consumers once shared libraries and pkg-config metadata are installed.
    for archive in Path(os.environ["LFS_SYSROOT"]).rglob("*.la"):
        archive.unlink()


def meson_install(source, name, options=(), host_tools=GLIB_HOST_TOOLS):
    build = Path(os.environ["LFS_WORKSPACE"]) / "build" / (name + "-meson")
    build.mkdir(parents=True, exist_ok=True)
    env = environment()
    target = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
    tool_entries = ""
    for tool, executable in host_tool_paths(env, host_tools).items():
        tool_entries += f"{tool} = '{executable}'\n"
    cross = build / "cross-file.ini"
    cross.write_text(
        "[binaries]\n"
        f"c = '{target}-gcc'\n"
        f"cpp = '{target}-g++'\n"
        f"ar = '{target}-ar'\n"
        f"strip = '{target}-strip'\n"
        "pkg-config = 'pkg-config'\n"
        + tool_entries
        + "\n[host_machine]\n"
        "system = 'linux'\n"
        "cpu_family = 'x86'\n"
        "cpu = 'i686'\n"
        "endian = 'little'\n"
        "\n[properties]\n"
        "needs_exe_wrapper = true\n",
        encoding="ascii",
    )
    # Native dependency discovery must not inherit target pkg-config paths.
    native = build / "native-file.ini"
    pkg_config = host_tool_paths(env, ("pkg-config",))["pkg-config"]
    tools = Path(env["LFS_WORKSPACE"]) / "tools"
    native.write_text(
        "[binaries]\n"
        "pkg-config = ['/usr/bin/env', '-u', 'PKG_CONFIG_SYSROOT_DIR', "
        f"'-u', 'PKG_CONFIG_LIBDIR', '{pkg_config}']\n"
        "\n[built-in options]\n"
        f"pkg_config_path = ['{tools / 'lib/pkgconfig'}', '{tools / 'share/pkgconfig'}']\n",
        encoding="ascii",
    )
    subprocess.run(
        [
            "meson",
            "setup",
            str(build),
            str(source),
            "--cross-file",
            str(cross),
            "--native-file",
            str(native),
            "--prefix=/usr",
            *options,
        ],
        env=env,
        check=True,
    )
    subprocess.run(["meson", "compile", "-C", str(build)], env=env, check=True)
    subprocess.run(
        ["meson", "install", "-C", str(build), "--destdir", os.environ["LFS_SYSROOT"]],
        env=env,
        check=True,
    )
