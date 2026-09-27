# GNU/MOS

GNU/MOS builds a 32-bit x86 operating system with the [MOS kernel](https://github.com/crazygeme/mos), GNU userspace, and an Xfce desktop. Package recipes compile the toolchain, system utilities, libraries, and applications from source, assemble a target sysroot, and install it into a GRUB-bootable disk image for QEMU.

![Xfce desktop running on GNU/MOS](docs/screen/xfce.png)

## System overview

- **Architecture:** i686 userspace, built with the `i686-lfs-linux-gnu` cross toolchain.
- **Core system:** MOS, glibc, GNU utilities, Bash, SysV init, and GRUB.
- **Desktop:** Xorg, XDM with PAM authentication, and Xfce with Thunar and xterm.
- **Applications:** Mousepad, MATE System Monitor, MATE Calculator, and FFplay in the desktop profile; FFmpeg and FFprobe in both profiles.
- **Networking:** an emulated e1000 adapter with host-provided DHCP, DNS, and IPv4 NAT.

The desktop profile starts graphical login in runlevel 5. The console profile starts in runlevel 3. Package versions, source locations, and build order are defined in the individual `src/packages/*/package.json` manifests.

## Host requirements

The build recipes target an x86-64 Linux host. Image setup also executes installed i686 programs, so the host must support 32-bit x86 execution.

Host tools include Bash, Python 3 with `tarfile` extraction-filter support, Git, a native C/C++ compiler, GNU Make, patch, archive utilities, and the build utilities required by individual package recipes. Host development dependencies depend on the selected packages; the command-line driver does not install distribution packages.

Image installation requires `sudo`, `qemu-img`, `sfdisk`, `losetup`, `mkfs.ext3`, and mount utilities. The QEMU launcher requires `qemu-system-x86_64`, access to KVM, `ip`, `sysctl`, `iptables`, and `dnsmasq`. Privileged operations use `sudo` to manage loop devices, mounts, and host networking.

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

Both profiles share `.workspace/sysroot/`, build artifacts, host tools, and `.workspace/qemu-hd/lfs.img`. The console build excludes packages marked with the `gui` profile; it does not remove GUI files already installed in the shared sysroot. `setup --no-gui` reformats the image partition and selects runlevel 3. Files stored only in that image partition are removed.

`./lfs run` boots the installed image configuration. Its `--no-gui` option does not change the image's runlevel or disable the QEMU display. The GRUB entry **LFS on MOS (console)** selects runlevel 3 independently of the configured default.

### Build control

| Command | Behavior |
| --- | --- |
| `./lfs status` | Display configured package versions, source/build state, and image presence. |
| `./lfs status --no-gui` | Display state for the console package selection. |
| `./lfs build` | Build the next package without a completion artifact. |
| `./lfs build --all` | Build all pending packages in manifest order. |
| `./lfs build --no-gui` | Build all pending console packages. |
| `./lfs build --all --rebuild` | Request confirmation, clear build state and the sysroot, and rebuild all packages. |
| `./lfs setup` | Copy system configuration, run postscripts for completed packages, and install the sysroot into the image. |
| `./lfs run` | Boot the image with QEMU and configure host networking for the session. |

Builds fetch missing sources automatically and skip packages with existing completion artifacts. Completion artifacts do not track recipe or source changes. `--rebuild` preserves downloaded archives and Git checkouts and cannot be combined with `--no-gui`.

Each package build starts with an empty `.workspace/build/` directory. Package builds must run sequentially within a workspace. Build logs are written to `.workspace/logs/<package>.log`.

### Image and virtual machine configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `LFS_IMAGE_SIZE` | `8G` | Raw disk size when `setup` creates a new image. |
| `LFS_RAM` | `2048` | Guest memory passed to QEMU with `-m`. |

The image uses a DOS partition table, one ext3 partition, and the GRUB `i386-pc` boot target. The launcher uses KVM, the host CPU model, two virtual CPUs, and an IDE disk. Serial output is written to `.workspace/krn.log`.

During execution, the launcher creates `lfs-tap0`, assigns the host address `10.0.6.1`, and serves the `10.0.6.0/24` subnet. It configures DHCP, DNS, forwarding, and NAT, then removes its network configuration when QEMU exits.

## Desktop and system configuration

XDM provides local graphical login on virtual terminal 2. Successful authentication starts Xfce under the selected system account; logging out returns to XDM. From a privileged guest shell, `telinit 3` stops graphical login and `telinit 5` starts it.

Xorg uses the VESA driver with an 800 × 600 default display mode and software rendering. This display configuration requires BIOS/VBE support and does not provide GPU acceleration.

System configuration resides in `src/sysroot/` and package `postscript.py` files. `./lfs setup` applies these files and postscripts before copying the sysroot into the image. Package postscripts configure services, desktop resources, and installation permissions.

System logs are stored in `/var/log/messages`, `/var/log/auth.log`, and `/var/log/kern.log`. Display-manager diagnostics are stored in `/var/log/xdm.log`, and desktop session output is appended to `~/.xsession-errors`.

## Repository layout

| Path | Contents |
| --- | --- |
| `lfs` | Command-line entry point. |
| `src/lfs.py` | Package orchestration, image installation, and QEMU launch logic. |
| `src/packages/` | Package manifests, build recipes, patches, and postscripts. |
| `src/package_lib.py` | Shared cross-compilation and package build helpers. |
| `src/sysroot/` | System configuration and filesystem overlay. |
| `docs/screen/` | System screenshots. |
| `.workspace/` | Downloaded sources, build trees, host tools, sysroot, artifacts, logs, and disk image. |

## Additional documentation

- [Package layout and system integration](src/packages/README.md)
- [MOS kernel package](src/packages/mos/README.md)
- [Xfce desktop and applications](src/packages/xfce/README.md)
