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

Runlevel 5 starts Xfce directly as root through `startx` on virtual terminal 2.
The init entry uses `once`; an exited session is not automatically restarted.
Runlevel 3 provides the console environment; the GRUB console entry selects
this runlevel.
`mos-xfce-session` sets the desktop environment variables and runs `startxfce4`
within `dbus-run-session`. Session bus lifetime follows the desktop session.
The selected display backend is X11.

The application menu provides Terminal (xterm). Xfce also uses xterm as its
default terminal emulator. DejaVu Sans Mono and UTF-8 are configured for
terminal text.

`./lfs build --no-gui` excludes the desktop and its GUI-only dependencies.
`./lfs setup` runs the session package postscript to compile installed GSettings
schemas before copying the sysroot into the bootable image.
