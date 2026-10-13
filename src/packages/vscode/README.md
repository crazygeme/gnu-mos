# Visual Studio Code

The package installs Visual Studio Code 1.140.0-1790759618 for x64 GUI images.
`/usr/share/code/code` starts the graphical application. `/usr/share/code/bin/code`
provides the command-line interface.

The package postscript installs a launcher at `/usr/share/code/code` and retains
the executable at `/usr/share/code/code.bin`. Graphical and command-line
invocations retain the application's sandbox defaults. The postscript assigns
root ownership and mode 4755 to `/usr/share/code/chrome-sandbox`.

MOS supports the SUID helper's chroot isolation and process dumpability controls.
Chromium namespace isolation and seccomp filtering are unavailable. The SUID
sandbox therefore provides filesystem isolation without these additional layers.

The configured desktop account uses a 60-second shell environment resolution
timeout through `application.shellEnvironmentResolutionTimeout` in
`~/.config/Code/User/settings.json`.
