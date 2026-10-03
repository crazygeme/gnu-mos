# Host QEMU Build Requirements

The `qemu-host` package builds QEMU 10.2.1 for the native x86-64 Linux host
and installs it into `.workspace/tools/qemu`. SDL, OpenGL, VirGL, and Pixman
support are required. The package depends on the `ninja` host build tool.

The recipe uses native host development libraries. Target i686 libraries in
`.workspace/sysroot` do not satisfy these requirements. Target compiler and
pkg-config environment overrides are removed before dependency detection.

On Debian and Ubuntu, `./lfs build` checks the manifest's `host-packages.apt`
list before preparing the QEMU source. Missing packages are installed through
`apt-get install --yes`, with `sudo` authentication when required. Fully
installed prerequisites do not trigger an installation command. Installation
failure stops the build before source preparation and compilation. Automatic
installation requires an APT-based host.

The equivalent manual installation command is:

```sh
sudo apt install pkg-config libsdl2-dev libvirglrenderer-dev libgbm-dev libdrm-dev libepoxy-dev libglib2.0-dev libpixman-1-dev zlib1g-dev python3-venv
```

Verify native library detection independently of the target environment:

```sh
env -u PKG_CONFIG_PATH -u PKG_CONFIG_LIBDIR -u PKG_CONFIG_SYSROOT_DIR \
    /usr/bin/pkg-config --print-errors --exists \
    glib-2.0 gio-2.0 pixman-1 epoxy sdl2 virglrenderer gbm libdrm zlib
```

A successful check produces no output and returns zero. Missing modules stop
the recipe before source extraction and compilation. The `sdl2`,
`virglrenderer`, `gbm`, and `libdrm` modules are supplied by `libsdl2-dev`,
`libvirglrenderer-dev`, `libgbm-dev`, and `libdrm-dev`, respectively.

Run `./lfs build` from the repository root to build the next pending package,
or `./lfs build --all` to process all pending packages in manifest order.
