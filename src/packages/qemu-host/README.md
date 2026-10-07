# Host QEMU Build Requirements

The `qemu-host` package builds QEMU 10.2.1 for the native x86-64 Linux host
and installs it into `.workspace/<arch>/tools/qemu`. SDL, OpenGL, VirGL, and Pixman
support are required. The package depends on `ninja` and `virglrenderer-host`.
The latter builds virglrenderer 1.3.0 with video support and installs it into
`.workspace/<arch>/tools/virglrenderer`. QEMU uses this library through its
pkg-config metadata and embedded runtime library search path.

The host renderer enables `video` and `unstable-apis`. Its pkg-config metadata
exports `VIRGL_RENDERER_UNSTABLE_APIS=1`, which exposes the video-enable flag
to QEMU through the installed header.

The recipe uses native host development libraries. Target libraries in
`.workspace/<arch>/sysroot` do not satisfy these requirements. Target compiler and
pkg-config environment overrides are removed before dependency detection.

On Debian and Ubuntu, `./lfs build` checks the manifest's `host-packages.apt`
list before preparing the QEMU source. Missing packages are installed through
`apt-get install --yes`, with `sudo` authentication when required. Fully
installed prerequisites do not trigger an installation command. Installation
failure stops the build before source preparation and compilation. Automatic
installation requires an APT-based host.

The equivalent manual installation command is:

```sh
sudo apt install pkg-config libsdl2-dev libgbm-dev libdrm-dev libepoxy-dev libglib2.0-dev libpixman-1-dev zlib1g-dev python3-venv libva-dev mesa-va-drivers
```

Verify native library detection independently of the target environment:

```sh
env -u PKG_CONFIG_LIBDIR -u PKG_CONFIG_SYSROOT_DIR \
    PKG_CONFIG_PATH="$(pwd)/.workspace/x64/tools/virglrenderer/lib/pkgconfig" \
    /usr/bin/pkg-config --print-errors --exists \
    glib-2.0 gio-2.0 pixman-1 epoxy sdl2 "virglrenderer >= 1.3.0" gbm libdrm zlib
```

A successful check produces no output and returns zero. Missing modules stop
the recipe before source extraction and compilation. The `sdl2`, `gbm`, and `libdrm` modules are supplied by `libsdl2-dev`,
`libgbm-dev`, and `libdrm-dev`, respectively. The `virglrenderer` module is
supplied by `virglrenderer-host`. The command selects the x64 workspace;
the x86 workspace uses `.workspace/x86/tools/virglrenderer/lib/pkgconfig`.

Run `./lfs build` from the repository root to build the next pending package,
or `./lfs build --all` to process all pending packages in manifest order.

The `virgl-video.patch` patch adds the `video-rendernode` device property,
provides its file descriptor to virglrenderer, and enables the renderer video
flag. The descriptor remains open until renderer cleanup.

The graphical launcher sets `video-rendernode` to `/dev/dri/renderD128`.
`MOS_VIDEO_RENDER_NODE` selects another host DRM render node. The host account
must have read and write access to this node. Virglrenderer requires a Mesa
Gallium VA-API driver with video codec support. Codec capabilities are
negotiated with the guest through the VirGL2 capability set.

On X11, the graphical launcher sets `SDL_VIDEO_X11_FORCE_EGL=1` because video
surface transfer uses EGL images. The host VA-API device must permit surface
sharing with the GPU used by the display backend.

Guest configuration and verification commands are documented in
[FFmpeg Video Acceleration](../ffmpeg/README.md).
