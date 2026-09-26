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

FFmpeg 8.0.3 provides `ffmpeg`, `ffprobe`, and shared media libraries in both
build profiles. `./lfs build --no-gui` includes these tools without SDL or X11
dependencies. The GUI profile adds the FFplay video player, SDL 2.32.10, and
ALSA library support. FFplay is available in the application menu and accepts
a filename with `ffplay -autoexit video.mp4`. FFmpeg can inspect media with
`ffprobe video.mp4` or convert it with
`ffmpeg -i input.mp4 -c:v mpeg4 -c:a aac output.mkv`.
The FFmpeg and FFplay recipes use the same source release and common build
configuration; the FFplay package installs only the player executable.

The console system uses the MOS kernel, GRUB, and sysvinit. Sysvinit runs
the runlevel 3 service scripts, displays startup results, and respawns
`agetty` on `/dev/tty1`.
The `sysklogd` service starts before the network and SSH services and accepts
local messages through `/dev/log`. Authentication messages are stored in
`/var/log/auth.log`, kernel messages in `/var/log/kern.log`, and other messages
in `/var/log/messages`. SSH uses its default syslog logging and log level.
MOS exposes kernel `printk()` records through `/dev/kmsg` and `/proc/kmsg`,
using the same record buffer as `klogctl()`. Sysklogd reads `/dev/kmsg` and
uses `/proc/kmsg` as a fallback. MOS diagnostic `klog()` output uses the serial
port. The service does not receive or forward network syslog messages.
The glibc postscript generates `C.utf8` locale data with the installed i686
`localedef` and dynamic loader. Setup requires an x86 Linux host capable of
running i686 executables. Login shells use `LANG=C.UTF-8` and
`LC_CTYPE=C.UTF-8`.
Manual pages are searched in `/usr/share/man` and `/usr/local/share/man`.
The target `groff` package formats manual pages, `gzip` reads compressed
manual pages, and the util-linux `more` command provides pagination.
The man-db configuration is `/etc/man_db.conf`, also available through
`/usr/etc/man_db.conf`.
The network service checks for `eth0` in `/proc/net/dev`. DHCP is provided by
the MOS kernel; service startup does not wait for address assignment.
When the `gui` kernel command-line token is present and the graphical
components are installed, the Xfce 4.20.0 session starts on `/dev/tty2` with
GTK 3.24.49 and a dedicated D-Bus session. The GUI profile includes Xfwm4,
Xfdesktop, the panel, settings manager, application finder, and Thunar.
