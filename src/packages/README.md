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
Both build modes use `.workspace/qemu-hd/lfs.img`. The graphical startup script
uses the `gui` kernel command-line token;
`./lfs run --no-gui` boots the console mode.
`./lfs run` connects an e1000 adapter through `lfs-tap0`. The host provides
DHCP, DNS, and IPv4 NAT on `10.0.6.0/24`; the guest uses `10.0.6.1` as its
name server.
`--rebuild` applies to the shared build state and cannot be combined with
`--no-gui`.

The console system uses the MOS kernel, GRUB, and sysvinit. Sysvinit runs
the runlevel 3 service scripts, displays startup results, and respawns
`agetty` on `/dev/tty1`.
When the `gui` kernel command-line token is present and the graphical
components are installed, the graphical session starts on `/dev/tty2`.
