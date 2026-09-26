# Xfce desktop

The GUI profile provides Xfce 4.20.0 with GTK 3.24.49 on Xorg. Components have
individual package manifests and build recipes. The configured desktop includes
Xfwm4, Xfdesktop, the panel, settings manager, application finder, Thunar, and
the session manager. Shared libraries include libxfce4util, Xfconf, libxfce4ui,
libxfce4windowing, Exo, and Garcon.

The dependency chain includes GTK 3, accessibility libraries, font and image
libraries, X11 extensions, startup notification, and display identification.
DejaVu fonts and the Adwaita icon theme provide desktop resources. The hardware
database is installed into both the sysroot and host tools prefix for native
display-information code generation.

The `gui` kernel command-line token starts Xorg on virtual terminal 2.
`mos-xfce-session` sets the desktop environment variables and runs `startxfce4`
within `dbus-run-session`. Session bus lifetime follows the desktop session.
The selected display backend is X11.

`./lfs build --no-gui` excludes the desktop and its GUI-only dependencies.
`./lfs setup` runs the session package postscript to compile installed GSettings
schemas before copying the sysroot into the bootable image.
