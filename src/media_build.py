"""Cross-build the FFmpeg package for the selected profile."""

import os
import subprocess
from pathlib import Path

from package_lib import archive_source, environment


def build_ffmpeg():
    player = os.environ.get("LFS_NO_GUI", "0") != "1"
    source = archive_source("ffmpeg", "ffmpeg-8.0.3.tar.xz", "ffmpeg-8.0.3")
    workspace = Path(os.environ["LFS_WORKSPACE"])
    sysroot = Path(os.environ["LFS_SYSROOT"])
    build = workspace / "build/ffmpeg-cross"
    build.mkdir(parents=True, exist_ok=True)
    env = environment()
    target = env.get("LFS_TARGET", "i686-lfs-linux-gnu")
    options = [
        "--prefix=/usr",
        "--libdir=/usr/lib",
        "--enable-cross-compile",
        "--cross-prefix=" + target + "-",
        "--arch=x86_64" if env.get("LFS_ARCH") == "x64" else "--arch=x86",
        "--cpu=x86-64" if env.get("LFS_ARCH") == "x64" else "--cpu=i686",
        "--target-os=linux",
        "--sysroot=" + str(sysroot),
        "--cc=" + env["CC"],
        "--cxx=" + env["CXX"],
        "--pkg-config=pkg-config",
        "--x86asmexe=" + str(workspace / "tools/bin/nasm"),
        "--extra-cflags=" + env["CFLAGS"],
        "--extra-ldflags=" + env["LDFLAGS"],
        "--enable-shared",
        "--disable-static",
        # Explicit external dependencies keep console binaries independent of
        # graphical libraries already present in a shared sysroot.
        "--disable-autodetect",
        "--enable-pthreads",
        "--enable-zlib",
        "--enable-bzlib",
        "--enable-lzma",
        "--enable-openssl",
        "--enable-version3",
    ]
    if player:
        options += [
            "--enable-sdl2",
            "--enable-libdrm",
            "--enable-vaapi",
            "--enable-ffplay",
            "--enable-ffmpeg",
            "--enable-ffprobe",
        ]
    else:
        options += [
            "--disable-sdl2",
            "--disable-libdrm",
            "--disable-vaapi",
            "--disable-ffplay",
            "--enable-ffmpeg",
            "--enable-ffprobe",
        ]
    subprocess.run(
        [str(source / "configure"), *options], cwd=build, env=env, check=True
    )
    subprocess.run(
        ["make", "-j4", "all"],
        cwd=build,
        env=env,
        check=True,
    )
    subprocess.run(
        ["make", "DESTDIR=" + str(sysroot), "install"],
        cwd=build,
        env=env,
        check=True,
    )
