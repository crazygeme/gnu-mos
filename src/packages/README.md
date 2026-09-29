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
Both build modes use `.workspace/qemu-hd/lfs.img`. `./lfs setup` configures
default runlevel 5; `./lfs setup --no-gui` configures default runlevel 3.
`./lfs run` boots the configuration installed in the shared image.
The GRUB entry `LFS on MOS (console)` passes `3` to `/sbin/init` and starts
text mode regardless of the configured default runlevel. MOS forwards standalone
`3` and `5` kernel command-line arguments to SysV init; the last matching
argument takes precedence.
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
the shared `/etc/rc3.d` service scripts in runlevels 3 and 5, displays startup
results, and respawns `agetty` on `/dev/tty1`. These shared init entries remain
active during transitions between runlevels 3 and 5.
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
In runlevel 5, XDM 1.1.17 provides a local graphical login on `/dev/tty2`.
PAM authenticates system accounts and creates missing home directories with
mode 0700. Successful login starts Xfce 4.20.0 as the authenticated user,
with GTK 3.24.49 and a dedicated D-Bus session. The GUI profile includes
Xfwm4, Xfdesktop, the panel, settings manager, application finder, Thunar,
and xterm 411. Xterm is the default terminal emulator and appears as Terminal
in the application menu. Logging out returns to the XDM login screen.
The GUI profile also includes MATE System Monitor 1.28.1, MATE Calculator
1.28.0, and Mousepad 0.6.5. Resource Manager opens CPU, memory, and network
usage graphs from the application menu. Calculator provides graphical
calculations, and Mousepad is the default text editor. Application commands
and supporting libraries are described in [Xfce desktop](xfce/README.md).
`telinit 3` stops the display manager; `telinit 5` starts it.
The init entry uses `once`, so an exited display manager is not automatically
restarted. XDM configuration resides in `/etc/X11/xdm`, PAM policy in
`/etc/pam.d/xdm`, and display-manager diagnostics in `/var/log/xdm.log`.
Session output is appended to `~/.xsession-errors`. XDMCP and X11 TCP
listeners are disabled.

Xorg 21.1.18 reads `/etc/X11/xorg.conf`. Its Meson cross configuration selects
the `poll` event backend because MOS does not implement `epoll_create1`.
The configured hostname is resolved through `/etc/hosts`, with the
`files` name service preceding DNS in `/etc/nsswitch.conf`.
The MOS configuration uses the Xorg modesetting driver, glamor, and Mesa
VirGL with 24-bit color depth. The driver probes the host's preferred size,
which QEMU configures as 2560 by 1440 pixels by default, and advertises a
preferred mode at a nominal 120 Hz. Xfce supports runtime resolution selection.
The DRM implementation does not provide page-flip
or vblank events; the mode frequency does not guarantee the presentation rate.
The GUI profile includes `xf86-input-keyboard` 1.9.0 and
`xf86-input-mouse` 1.9.5, installed into `/usr/lib/xorg/modules`.
The keyboard uses the console `kbd` driver with the `base` XKB rules and a
US PC105 layout. The keyboard package provides the Linux console backend
required by MOS; the kernel does not expose evdev input event devices.
The mouse package provides the Linux PS/2 backend and uses the IMPS/2
protocol on `/dev/input/mice`,
including wheel buttons 4 and 5. Device and GPU automatic addition are
disabled; the server layout selects the configured devices explicitly.
Core X fonts use the server's `built-ins` font path. Desktop applications
use the installed DejaVu fonts through Fontconfig. The desktop graphics path
uses the `qemu-host` package (QEMU 10.2.1) and requires hardware-accelerated
host OpenGL. The package installs into `.workspace/tools/qemu` and applies
`sdl-gl-scanout.patch` so SDL refresh preserves active OpenGL scanout.
`sdl-relative-pointer.patch` forwards SDL relative motion without window scaling
to preserve small PS/2 pointer movements.
Its native development dependencies are listed in the root README. Mesa is
configured with the VirGL Gallium driver. The `mesa-utils` package supplies
`glxinfo`, `glxgears`, and `eglinfo`.
The `xshmfence` package uses `/dev/shm` for DRI3 synchronization files.
Boot initialization mounts tmpfs there and sets directory permissions to 1777.

Xorg uses the setuid-root `/usr/libexec/Xorg.wrap` entry point with
`allowed_users=console` and `needs_root_rights=yes` in
`/etc/X11/Xwrapper.config`. The package postscript sets the wrapper and
server ownership and creates the X11 and ICE socket directories with mode
1777. Before graphical services start, boot initialization removes the
display `:0` lock files and socket from `/tmp`, recreates the socket
directories, and mounts sysfs on `/sys`.
Before login, the Xorg ownership script assigns `/usr` and `/etc` to root
and removes group and other write permissions from their regular files and
directories. This protects the privileged server, libraries, modules, and
configuration while leaving the host build sysroot writable for package builds.
The wrapper receives mode 4755 only after ownership initialization completes.
MOS exposes PCI configuration space, device attributes, and BAR resources
under `/sys/bus/pci/devices`. Memory BAR mappings are restricted to root
and to the 32-bit physical address space. Libpciaccess enables its
`/dev/mem` ROM fallback for BIOS video initialization.
Xorg uses explicitly configured input devices without the udev discovery
backend. XKB data resides in `/usr/share/X11/xkb`, compiled keymaps in
`/var/lib/xkb`, and the XKB compiler in `/usr/bin`.

The xinit package requires GNU sed 4.9 for the `startx` authentication setup.
MOS exposes fixed x86 platform I/O resources through `/proc/ioports`; this
interface does not enumerate PCI BAR allocations. Xorg reads the hexadecimal
port ranges to exclude keyboard and timer ports from direct I/O access.
The Xorg package applies `linux-ioports.patch` to validate the input and report
an unavailable `/proc/ioports` without dereferencing a null stream.

The MOS `/dev/mem` interface addresses the 32-bit physical address space,
including PCI expansion ROMs above installed RAM. Positioned I/O preserves
64-bit offsets and rejects negative offsets; reads at or above 4 GiB return
EOF. Libpciaccess applies `rom-read-progress.patch` so ROM reads advance the
output buffer after short reads, retry interrupted reads, and return `EIO`
on premature EOF.

Xorg resolves software DRI drivers in `/usr/lib/dri` on the target system.
The `xrdb` package installs the X resource database utility and uses
`/usr/bin/cpp` for preprocessing. Xfce session setup depends on `xrdb`.
MOS accepts `SOCK_CLOEXEC` and `SOCK_NONBLOCK` on Unix socket pairs and applies
the flags to both descriptors. The 32-bit and time64 futex interfaces support
WAIT, WAKE, WAIT_BITSET, and WAKE_BITSET; bitset waits accept absolute monotonic
or realtime deadlines. Futex wait queues are scoped to the process address
space and do not provide cross-process shared-memory synchronization.

MOS implements `SO_PEERCRED` for Unix sockets. Connected stream sockets retain
the peer PID and effective UID/GID captured at connection establishment;
socket pairs retain the creator credentials. Credential snapshots remain
available after peer closure and support D-Bus EXTERNAL authentication.

Unix socket `recv`, `recvfrom`, and `recvmsg` share the locked receive path.
Consuming buffered data wakes the peer so that blocked writes and writable
poll events can proceed when receive-buffer space becomes available.

MOS detaches socket and poll wait registrations before closing descriptors or
releasing an exiting thread's kernel stack. Explicit `SCM_CREDENTIALS` messages
are accepted for the sender's PID and real, effective, or saved UID/GID. With
`SO_PASSCRED` disabled, validated credentials are discarded and the payload is
transferred; receivers can query connection credentials using `SO_PEERCRED`.
