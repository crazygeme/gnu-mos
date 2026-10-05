# Xfce desktop

The GUI profile provides Xfce 4.20.0 with GTK 3.24.49 on Xorg. Components have
individual package manifests and build recipes. The configured desktop includes
Xfwm4, Xfdesktop, the panel, settings manager, application finder, Thunar,
the session manager, and xterm 411. Shared libraries include libxfce4util,
Xfconf, libxfce4ui, libxfce4windowing, Exo, and Garcon.

The dependency chain includes GTK 3, accessibility libraries, font and image
libraries, X11 extensions, startup notification, and display identification.
DejaVu fonts and the Adwaita icon theme provide desktop resources. The hardware
database is installed into both the sysroot and host tools prefix for native
display-information code generation.

Runlevel 5 starts XDM 1.1.17 on virtual terminal 2. PAM authenticates system
accounts and creates missing home directories. The authenticated user runs
Xfce through `/etc/X11/xdm/Xsession`; logout returns to the login screen.
The init entry uses `once`; an exited display manager is not automatically
restarted. XDM accepts local logins only.
Runlevel 3 provides the console environment; the GRUB console entry selects
this runlevel.
`mos-xfce-session` sets the desktop environment variables and runs `startxfce4`
within `dbus-run-session`. Session bus lifetime follows the desktop session.
The selected display backend is X11.

Xorg initially selects the preferred mode reported by the VirtIO-GPU driver.
The Xfce default display profile selects 1920 × 1080 on `Virtual-1`, with a
nominal refresh rate of 120 Hz. Xfce display settings can select other
advertised resolutions at runtime. GTK uses a window scaling factor of 1;
the default output has no RandR resampling.
Xft uses 96 DPI for clients such as xterm. GTK uses `Gdk/UnscaledDPI` of
98304 (96 × 1024) with its window scaling factor, giving both font paths an
effective 96 DPI.
The system Xsettings configuration is installed from `xsettings.xml`
in `src/sysroot/etc/xdg/xfce4/xfconf/xfce-perchannel-xml`.
The system `displays.xml` channel defines the default output mode. The
`ezheng` account has the same default display profile in
`~/.config/xfce4/xfconf/xfce-perchannel-xml/displays.xml`. Per-user Xfconf
settings can override the system defaults.
The default cursor theme is Adwaita with a nominal size of 24 pixels.
Xsettings and `/etc/X11/Xresources` configure the cursor theme and size for
GTK and Xcursor clients.

ICE authentication uses iceauth 1.0.10 at `/usr/bin/iceauth`. Xfce session
clients authenticate through ICE to participate in session saving and logout.
The session manager build uses this target path explicitly.

The session logout dialog provides shutdown and restart through the Xfce
polkit fallback. The GUI profile includes polkit 126 and Duktape 2.7.0.
The system D-Bus and polkit services start before graphical login. Members
of the `sudo` group, including `ezheng`, are authorized to invoke the Xfce
shutdown helper without an additional password. Authorization uses group
membership for both local and remote processes; no session-tracking daemon
is configured. Other polkit actions retain their individual policies.
`/etc/shells` lists the installed Bash and POSIX shell paths accepted by
`pkexec` when validating the session's `SHELL` environment variable.

Shutdown enters SysV runlevel 0 and restart enters runlevel 6. Both runlevels
terminate remaining processes, synchronize filesystem data, unmount mounted
filesystems where possible, and remount the root filesystem read-only before
the privileged terminal poweroff or reboot command.
MOS powers off the configured QEMU PIIX4 machine through its PCI-discovered
ACPI power-management registers. The terminal reboot syscall requires
effective UID 0 and performs the hardware reset from the runlevel script.

The default wallpaper is `/usr/share/backgrounds/xfce/xfce-blue.jpg`.
The configured image loaders support JPEG and PNG. SVG wallpaper decoding
is unavailable.

The application menu provides Terminal (xterm). Xfce also uses xterm as its
default terminal emulator. Fira Code 6.002 Regular at 13 points and UTF-8 are
configured for terminal text. The variable font is installed from
`src/sysroot/usr/share/fonts/fira-code/FiraCode_VF.ttf`; its SIL Open Font
License 1.1 is included in the same directory.

The application menu includes the following GTK 3 applications:

| Application | Version | Command | Function |
| --- | --- | --- | --- |
| Resource Manager (MATE System Monitor) | 1.28.1 | `mate-system-monitor --show-resources-tab` | CPU history, memory and swap usage, network transfer rates, and process information |
| Calculator (MATE Calculator) | 1.28.0 | `mate-calc` | Arithmetic, scientific, financial, and programming calculations |
| Mousepad | 0.6.5 | `mousepad` | Tabbed text editing, syntax highlighting, and search and replacement |

Resource Manager opens the Resources tab from the application menu. LibGTop
2.40.0 reads the kernel's process and resource statistics, including
`/proc/stat`, `/proc/meminfo`, and `/proc/net/dev`. Displayed measurements are
limited to the statistics exposed by the MOS kernel.

The calculator and resource-manager menu entries use the GSettings keyfile
backend. Mousepad is configured to use that backend and is the default
application for plain text and shell-script files. GtkSourceView 4.8.4
provides its text editing component. The gspell plugin uses Enchant with the
Hunspell provider and ICU 77.1; dictionaries must be installed separately to enable
language-specific spelling checks.

The resource manager uses gtkmm 3.24.10 and librsvg 2.40.21. The librsvg
package provides the SVG rendering library without a GdkPixbuf loader.
The `libxml2-python-host` and `itstool` packages provide host tools for
building the MATE application help files.

`./lfs build --no-gui` excludes the desktop and its GUI-only dependencies.
`./lfs setup` runs the session package postscript to compile installed GSettings
schemas before copying the sysroot into the bootable image. The postscript
runs the installed schema compiler through the selected architecture's dynamic
loader: `ld-linux.so.2` for x86 or `ld-linux-x86-64.so.2` for x64.
