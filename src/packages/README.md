# Package Layout

Each package directory contains a `package.json` manifest and a `build.py`
recipe.

`source=archive` requires `url` and `archive`. The fetch stage downloads the
archive into `.workspace/sources/` and the build recipe consumes that file.

`source=git` requires `git`. The fetch stage clones the selected branch into
`.workspace/sources/<name>/` and the build recipe consumes that checkout.

`source=meta` identifies a package that creates system integration files or
coordinates components without downloading a standalone source archive. It is
not used as a substitute for missing source packages.

Every compiled userspace component must have its own manifest and build recipe.
The package list is intentionally explicit so each download, version, build
order, and artifact is inspectable.

The `ninja` and `meson` source packages install host build tools into
`.workspace/tools/bin/` before Meson-based packages are built.

Packages with `"profiles": ["gui"]` are included in the full build and
excluded from `./lfs build --no-gui`, which builds all console packages. The
console build uses `.workspace/sysroot/`, `.workspace/tools/`, and
`.workspace/artifacts/`. Completed packages are shared between build modes.
Both build modes use `.workspace/qemu-hd/lfs.img`. Sysvinit selects the
console or graphical startup script from the `gui` kernel command-line token;
`./lfs run --no-gui` boots the console mode.
`--rebuild` applies to the shared build state and cannot be combined with
`--no-gui`.

The console system uses the MOS kernel, GRUB, and sysvinit. Sysvinit starts
the runlevel 3 console shell on `/dev/tty1`.
