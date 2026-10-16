# GNU/MOS

GNU/MOS builds 32-bit x86 and 64-bit x86 operating systems with the [MOS kernel](https://github.com/crazygeme/mos), GNU userspace, and an Xfce desktop. Package procedures compile source packages or extract configured Debian binary packages, assemble a target sysroot, and install it into a GRUB-bootable disk image for QEMU.

![Xfce desktop running on GNU/MOS](docs/screen/xfce.png)

## System overview

- **Architectures:** `x86` uses i686 userspace and `i686-lfs-linux-gnu`; `x64` uses x86-64 userspace and `x86_64-lfs-linux-gnu`. The default architecture is `x64`.
- **Core system:** MOS, glibc, GNU utilities, Bash, SysV init, and GRUB.
- **Desktop:** Xorg, XDM with PAM authentication, and Xfce with Thunar and xterm.
- **Applications:** Mousepad, MATE System Monitor, MATE Calculator, and FFplay in the desktop profile; FFmpeg and FFprobe in both profiles. The x64 desktop profile also extracts Microsoft Edge and Visual Studio Code Debian binary packages; application execution requires compatible runtime libraries and MOS interfaces.
- **Networking:** an emulated e1000 adapter with host-provided DHCP, DNS, and IPv4 NAT.
- **Network and development tools:** GNU Make and GNU Wget in both
  profiles, with a Mozilla-derived certificate trust store for HTTPS.

The desktop profile starts graphical login in runlevel 5. The console profile starts in runlevel 3. Package versions, source locations, and build order are defined in the individual `src/packages/*/package.json` manifests.

## Host requirements

The build recipes target an x86-64 Linux host. Image setup executes installed target programs. The x86 profile requires host support for 32-bit x86 execution; the x64 profile requires x86-64 execution.

Host tools include Bash, Python 3 with `tarfile` extraction-filter support, Git, a native C/C++ compiler, GNU Make, patch, archive utilities, and the build utilities required by individual package recipes. Host development dependencies depend on the selected packages. Before downloading sources or compiling, `./lfs build` collects the declared APT host dependencies of all packages to be built and installs missing distribution packages in one `apt-get` invocation, using `sudo` when required. Installed dependencies do not trigger installation or authentication.

Debian binary packages require host `dpkg-deb` and GNU tar. They use
`source: "deb"` manifests and extract into `.workspace/<arch>/sysroot/` without
compilation or Debian maintainer-script execution. Package identity, version,
and architecture are checked before extraction. The Microsoft Edge and Visual
Studio Code examples also verify pinned SHA256 checksums. The package procedure
does not resolve Debian runtime dependencies. See
[Package layout and system integration](src/packages/README.md) for manifest
fields and extraction behavior.

Image installation requires `sudo`, `qemu-img`, `sfdisk`, `losetup`, `mkfs.ext3`, `debugfs`, and mount utilities. The console launcher requires the host `qemu-system-x86_64`. Both launch profiles require access to KVM, `ip`, `sysctl`, `iptables`, and `dnsmasq`. Privileged operations use `sudo` to manage loop devices, mounts, and host networking.

The GUI profile builds QEMU 10.2.1 through `qemu-host`, installs it in `.workspace/<arch>/tools/qemu`, and uses that executable for desktop launches. Its SDL refresh path preserves active OpenGL scanout. The desktop launcher uses `virtio-vga-gl` with `-display sdl,gl=on,full-screen=on`. The window starts in borderless desktop fullscreen mode at the host desktop resolution. Relative-pointer movement is forwarded without window scaling, preserving small movements in both windowed and fullscreen modes. `Ctrl+Alt+F` toggles fullscreen mode. The host graphics driver must provide hardware-accelerated OpenGL. An explicit `-display` argument overrides the default display backend and fullscreen setting.

The launcher provides USB Audio playback using QEMU's SDL audio backend.
`MOS_AUDIO_BACKEND` selects another backend supported by the configured QEMU
executable. Explicit `-audio` or `-audiodev` arguments replace the default audio
configuration and must include the required guest sound device. The USB Audio
Class 1 driver exposes stereo 48 kHz signed 16-bit little-endian PCM through
`/dev/dsp`, `/dev/audio`, and `/dev/mixer`. The ALSA default device uses the OSS
plugin and converts application sample rates and formats to this PCM format.
The Xfce session defaults SDL applications to the `dsp` audio driver. An explicit
`SDL_AUDIODRIVER` value overrides that default. USB microphone capture, UAC2,
and asynchronous feedback endpoints are not supported.

The `qemu-host` and `virglrenderer-host` recipes use native host development libraries. On Debian or Ubuntu, `./lfs build` checks and installs their declared dependencies during build preparation when these packages are pending. Installation may require a sudo password. The equivalent manual command is:

```sh
sudo apt install pkg-config libsdl2-dev libgbm-dev libdrm-dev libepoxy-dev libglib2.0-dev libpixman-1-dev zlib1g-dev python3-venv libva-dev mesa-va-drivers libusb-1.0-0-dev acl
```

The recipe requires SDL, OpenGL, and VirGL support during configuration. Host QEMU installation does not require copying files into the guest image.

The `virglrenderer-host` package supplies virglrenderer 1.3.0 with VA-API video
support. Graphical FFmpeg builds use the guest libva and Mesa VirGL video
driver. Hardware codec operations require a compatible host Mesa VA-API driver
and explicit FFmpeg acceleration options. Configuration and verification are
documented in [FFmpeg Video Acceleration](src/packages/ffmpeg/README.md).

## Build and run

Run commands from the repository root. To build the desktop system, install the image, and start the virtual machine:

```sh
./lfs build --all
./lfs setup
./lfs run
```

To build and install the console profile:

```sh
./lfs build --no-gui
./lfs setup --no-gui
./lfs run
```

Within each architecture, both profiles share `.workspace/<arch>/sysroot/`, build artifacts, host tools, and `.workspace/<arch>/qemu-hd/lfs.img`. The console build excludes packages marked with the `gui` profile; it does not remove GUI files already installed in the shared sysroot. `setup --no-gui` reformats the image partition and selects runlevel 3. Files stored only in that image partition are removed.

`./lfs run` boots the installed image configuration. Its `--no-gui` option does not change the image's runlevel or disable the QEMU display. The GRUB entry **LFS on MOS (console)** selects runlevel 3 independently of the configured default.

### Architecture selection

`--arch x86|x64` selects the architecture for `build`, `setup`, `status`, and
`run`. Commands without `--arch` select `x64`; `--arch x86` selects the x86 workspace. The option is accepted before or after the subcommand. Source archives
and the MOS checkout are shared under `.workspace/sources/`; each architecture
has its own sysroot, tools, completion records, caches, logs, mount directory,
and disk image under `.workspace/<arch>/`. Source fetching uses a shared lock for each source file or checkout, preventing duplicate downloads during
concurrent architecture builds. Go module sources use `.workspace/sources/go-modules/`.

```sh
./lfs build --arch x64 --all
./lfs setup --arch x64
./lfs run --arch x64
./lfs status --arch x86
```

Commands operate directly on `.workspace/<arch>/`. Host tools are compiled
with installation paths for the selected architecture. Completion versions
control package rebuild selection.
`stats` is an alias for `status`.

The x64 sysroot uses `/usr/lib` for libraries, with `/lib64` and `/usr/lib64`
aliases for the x86-64 ABI. MOS installs the x86 ELF kernel or the x64 flat
Multiboot image as `/boot/kernel`. Both architectures use BIOS GRUB `i386-pc`.

### Build control

Bash completion is installed automatically when `./lfs` is executed. The launcher
links `completions/lfs.bash` into
`${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/lfs`.
When `BASH_COMPLETION_USER_DIR` is configured, its first nonempty directory is
used with the `completions/lfs` suffix. Existing files and links are preserved;
installation failures do not interrupt the requested command.

With `bash-completion` enabled in the interactive shell, completion loads on
demand for `./lfs` and `lfs` without a separate installation command or manual
`source`. Completion provides subcommands and their options, omits options
already present, and uses filename completion for QEMU arguments after
`./lfs run --`.

| Command | Behavior |
| --- | --- |
| `./lfs status` | Display configured package versions, source/build state, and image presence. |
| `./lfs status --no-gui` | Display state for the console package selection. |
| `./lfs build` | Build the next package with a missing or outdated completion artifact. |
| `./lfs build --all` | Build all pending packages in manifest order. |
| `./lfs build --no-gui` | Build all pending console packages. |
| `./lfs build --all --rebuild` | Delete all completion markers and build all pending packages in manifest order. |
| `./lfs setup` | Copy system configuration, run postscripts for completed packages, and install the sysroot into the image. |
| `./lfs run` | Boot the image with QEMU and configure host networking for the session. |

Before compilation, builds fetch and validate sources for all packages to be built, using four concurrent download workers. Compilation starts only after all source preparation succeeds. The default command prepares the next pending package; `--all` and `--no-gui` prepare all pending packages in their selected profile. Cached sources are reused. Interactive terminals display each active download on a separate progress line and retain completion or failure messages. Redirected output records download start and completion or failure on separate lines. Git clone output is recorded in `.workspace/<arch>/logs/<package>-download.log`. Each package defines a positive integer build version in `src/packages/<package>/version`, independently of the upstream software version in `package.json`. Completion artifacts record this build version in their JSON `version` field. Both `status` and `build` consider a package built when its completion version is at least its configured build version. A missing artifact or an older completion version requires compilation. An existing artifact without a `version` field, including an empty artifact, is assigned the configured build version and remains built. Changes requiring recompilation must increment the affected package's build version. `--rebuild` deletes all `*.done` files recursively under `.workspace/<arch>/artifacts/` without prompting, then follows the normal build flow. The deletion preserves all other files. Normal package selection and stopping rules apply: the default builds one package, `--all` builds all pending packages, and `--no-gui` builds all pending console packages. All completion markers for the selected architecture are deleted even when `--no-gui` is selected.

FFmpeg, FFprobe, and FFplay are outputs of the single `ffmpeg` package.
The GUI profile builds all three together; the console profile omits FFplay.
The completion record identifies the built profile, so a console build is
pending when the GUI profile is selected.

Each package build starts with an empty `.workspace/<arch>/build/` directory. Package builds must run sequentially within each architecture workspace. Different architectures use separate build trees and installation paths. Build logs are written to `.workspace/<arch>/logs/<package>.log`.

Autoconf recipes retain successful configuration test results under
`.workspace/<arch>/configure-cache/<package>/`. Each configure invocation uses a cache
selected by its command, build directory, configure script, package files,
environment, compiler and tool metadata, explicit `CONFIG_SITE` contents, and
other installed package completion records. Native and cross configurations
use separate entries. A matching cache is restored into the fresh build tree;
configure still runs to generate Makefiles and configuration headers. Only
checks implemented with Autoconf cache variables reuse their results. Failed
configure invocations do not replace the persistent cache.

The configuration cache survives build-tree cleanup and `--rebuild`.
Changes to cache inputs select a separate entry. Host header or library changes
outside the package build workflow require removing
`.workspace/<arch>/configure-cache/` before configuration. Removing a package's cache
directory forces fresh checks for that package on its next build. Build systems
without Autoconf cache support, including QEMU and zlib, retain their own
configuration behavior.

### Image and virtual machine configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `LFS_IMAGE_SIZE` | `8G` | Raw disk size when `setup` creates a new image. |
| `LFS_RAM` | `4096` | Guest memory passed to QEMU with `-m`. |

The image uses a DOS partition table, one ext3 partition, and the GRUB `i386-pc` boot target. The launcher uses KVM, the host CPU model, two virtual CPUs, and an IDE disk. Serial output is written to `.workspace/<arch>/krn.log`.

The launcher sets `opt/org.seabios/pci64=0` through QEMU firmware configuration to keep PCI memory resources below 4 GiB, within the i686 kernel's device mapping range.

During execution, the launcher creates `lfs-tap0`, assigns the host address `10.0.6.1`, and serves the `10.0.6.0/24` subnet. It configures DHCP, DNS, forwarding, and NAT, then removes its network configuration when QEMU exits.

### USB input and data storage

The QEMU launcher provides an xHCI controller, a USB keyboard, and a relative
USB mouse. The emulated PS/2 controller is disabled. The system disk remains
attached through IDE. USB mass storage is optional and is not attached by
default.

`MOS_USB_IMAGE` attaches an existing raw data-device file as a removable USB
mass-storage device. The launcher does not create or format USB disk images.

```sh
MOS_USB_IMAGE=/path/to/usb.img ./lfs run
```

In Xfce, the MOS GIO volume monitor exposes USB volumes in Thunar and on the
desktop. The session automounter mounts ext3 and ext4 volumes under
`/media/mos/<device>-<attachment-id>` at login and on insertion. A manually
unmounted volume remains unmounted until a mount action, a new session, or
reinsertion. The volume context menu provides mounting and unmounting.

The `org.mos.Storage1` system D-Bus service discovers USB block devices through
sysfs, probes filesystem labels and UUIDs with libblkid, and performs privileged
mount operations. Polkit grants mount and unmount operations to members of
`sudo`. The service accepts attachment identities rather than arbitrary device
paths or mount options. Mounts use `nosuid` and `nodev` flags. POSIX filesystem
permissions remain effective after mounting. Removal retires the associated
mount and reinsertion creates a distinct volume identity.

Outside a graphical session, a permitted account can mount an attached USB volume
with `gio mount -d /dev/sda`. `gio mount -li` lists the volume and its current
mount path; `gio mount -u <mount-path>` unmounts it. Administrative manual
mounting remains available when the volume is not mounted by the desktop:

```sh
mkdir -p /mnt/usb
mount -t ext3 /dev/sda /mnt/usb
sync
umount /mnt/usb
```

For a data device attached with `MOS_USB_IMAGE`, the QEMU monitor can
disconnect and reconnect the device while retaining its backing file:

```text
device_del usb-disk
device_add usb-storage,id=usb-disk,bus=usb.0,port=3,drive=usbdata,removable=true
```

The keyboard and mouse device identifiers are `usb-keyboard` and `usb-mouse`.

USB disks use `/dev/sda`, `/dev/sdb`, and subsequent SCSI-style device names.
MBR primary partitions use names such as `/dev/sda1`. Interface identities and
driver bindings are exposed under `/sys/bus/usb/devices`. Block-device metadata
is exposed under `/sys/class/block`, `/sys/block`, and `/sys/dev/block`. The
`mos_generation` attribute distinguishes USB attachments when device numbers
are reused.

MOS enumerates devices connected directly to xHCI root ports during startup
and after runtime attachment. Removal cancels device I/O, removes its device
nodes and USB interface bindings, and releases pressed HID keys and buttons.
An open descriptor for a removed disk returns `ENODEV` for reads and writes;
it does not reference a reinserted disk. Disconnected device objects remain
allocated until their final open descriptor or filesystem handle is closed.
Unmount a USB filesystem before removing its device to commit pending writes.
The desktop storage service detaches its mounts after removal. Filesystems
mounted administratively require administrative cleanup after removal. External
The xHCI transport supports external hubs, nested routes, downstream port power,
reset, connection changes, and recursive device removal. USB2 hubs use the
single transaction translator alternate setting. Hub status interrupts have a
periodic status-check fallback. A route supports up to five external hubs;
controllers expose up to 127 device slots. HID support covers boot-protocol
keyboards and relative mice; mouse reports with
an additional wheel byte are accepted. Storage support covers Bulk-Only
Transport with the SCSI transparent command set, LUN 0, 512-byte sectors, and
capacities below 2 TiB. UAS, GPT partition discovery, extended partitions, and
non-boot HID report formats are not supported.

### USB isochronous transfers and cameras

The transport configures control, bulk, interrupt, and isochronous endpoints.
Interface alternate settings are retained during descriptor parsing and can be
selected independently. Isochronous submissions contain up to 256 service
intervals and 1 MiB of data. Two submissions can remain queued per endpoint;
each packet reports its actual length and completion status. Device removal
cancels pending submissions before reclaiming DMA buffers.

The launcher reserves USB port 4 for audio and port 5 for a host camera. The
xHCI controller provides eight USB2 and eight USB3 ports. `MOS_USB_CAMERA=auto`
selects the first USB camera exposed through the host video-device inventory.
`MOS_USB_CAMERA=BUS:PORT` selects a physical USB port, such as `3:6` or `3:6.2`.
`MOS_USB_CAMERA=none` omits camera passthrough. The host `acl` package supplies
`getfacl` and `setfacl`; the launcher temporarily grants the invoking account
read/write access to the selected USB device when required and restores its
ACL after QEMU exits. The selected camera is assigned to the guest while QEMU
runs and cannot simultaneously serve a host camera application.

The UVC driver exposes supported MJPEG and YUYV capture interfaces as
`/dev/video0` through `/dev/video3`. V4L2 supports format and frame-size
selection, `read`, polling, and shared `mmap` streaming with up to four queued
frame buffers. Capture retains complete frames and discards damaged or
incomplete frames. The maximum frame buffer is 4 MiB. USERPTR, DMA-BUF, UVC
extension controls, and infrared-specific pixel formats are not supported.

Guvcview 2.2.2 is built from source with GTK3 and SDL2, using the configured
FFmpeg, libv4l, libusb, and PortAudio libraries. Continuous preview uses V4L2
`mmap` capture with MJPEG compression:

```sh
guvcview --device=/dev/video0 --capture=mmap --format=MJPG --resolution=320x240 --audio=none
```

Additional emulated hubs can use free ports, for example:

```sh
./lfs run -- -device usb-hub,id=usb-hub,bus=usb.0,port=6
```

The host-side `tests/usb_hub.py` runner validates downstream disk removal and
hub-subtree replacement using QMP and the guest `usb_hotplug` test. Its test
topology uses hubs at ports `6` and `6.1`, with a keyboard at `6.1.1`, a mouse
at `6.1.2`, and the `usb-disk` storage device at `6.1.3`. The `usbdata` backing
node requires an existing image selected with `MOS_USB_IMAGE`. Guest audio and camera
checks are available in `tests/guest/usb_audio.c`, `usb_alsa.c`, and
`usb_camera.c`.

## Desktop and system configuration

XDM provides local graphical login on virtual terminal 2. Successful authentication starts Xfce under the selected system account; logging out returns to XDM. From a privileged guest shell, `telinit 3` stops graphical login and `telinit 5` starts it.

Xorg uses the modesetting driver with glamor and the Mesa VirGL driver. QEMU supplies a default preferred size of 2560 × 1440; the driver probes this size and exposes a preferred mode at a nominal 120 Hz with 24-bit color depth. Xfce display settings support runtime resolution changes. Rendering executes on the host GPU. The DRM implementation does not provide page-flip or vblank events; the advertised mode frequency does not guarantee a 120 FPS presentation rate. Presentation also depends on the host display and QEMU frontend.

The desktop provides `glxinfo`, `glxgears`, `eglinfo`, and `mos-gpu-info`. A zero video-memory value means that the queried capacity is unavailable when VirGL does not expose the corresponding host capability; it is not a measurement of allocated graphics memory. `mos-gpu-info` checks direct rendering and the renderer string. Shared graphics buffers use implicit synchronization between VirGL contexts.

System configuration resides in `src/sysroot/` and package `postscript.py` files. `./lfs setup` applies these files and postscripts before copying the sysroot into the image. Package postscripts configure services, desktop resources, and installation permissions.

System logs are stored in `/var/log/messages`, `/var/log/auth.log`, and `/var/log/kern.log`. Display-manager diagnostics are stored in `/var/log/xdm.log`, and desktop session output is appended to `~/.xsession-errors`.

## Repository layout

| Path | Contents |
| --- | --- |
| `lfs` | Command-line entry point. |
| `src/lfs.py` | Package orchestration, image installation, and QEMU launch logic. |
| `src/packages/` | Package manifests, build recipes, patches, and postscripts. |
| `src/package_lib.py` | Shared cross-compilation and package build helpers. |
| `src/deb_package.py` | Debian binary package validation and filesystem extraction. |
| `src/sysroot/` | System configuration and filesystem overlay. |
| `docs/screen/` | System screenshots. |
| `.workspace/sources/` | Shared source archives, Debian binary archives, and checkouts. |
| `.workspace/x86/`, `.workspace/x64/` | Architecture-specific build trees, host tools, sysroot, artifacts, caches, logs, and disk image. |

## Additional documentation

- [Package layout and system integration](src/packages/README.md)
- [MOS kernel package](src/packages/mos/README.md)
- [GNU Wget and HTTPS](src/packages/wget/README.md)
- [GNU Make](src/packages/make/README.md)
- [Xfce desktop and applications](src/packages/xfce/README.md)
