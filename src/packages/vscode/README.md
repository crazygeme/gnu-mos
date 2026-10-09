# Visual Studio Code

The package installs Visual Studio Code 1.140.0-1790759618 for x64 GUI images.
`/usr/share/code/code` starts the graphical application. `/usr/share/code/bin/code`
provides the command-line interface.

The package postscript installs a launcher at `/usr/share/code/code` and retains
the executable at `/usr/share/code/code.bin`. The launcher adds `--no-sandbox`
to graphical and command-line invocations. MOS does not implement Chromium's
namespace and seccomp sandbox isolation; Code processes therefore run without
Chromium sandbox protection.

The configured desktop account uses a 60-second shell environment resolution
timeout through `application.shellEnvironmentResolutionTimeout` in
`~/.config/Code/User/settings.json`.
