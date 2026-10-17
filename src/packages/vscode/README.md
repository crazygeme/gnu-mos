# Visual Studio Code

The package installs Visual Studio Code 1.140.0-1790759618 for x64 GUI images.
`/usr/share/code/code` starts the graphical application. `/usr/share/code/bin/code`
provides the command-line interface.

The package postscript installs a launcher at `/usr/share/code/code` and retains
the executable at `/usr/share/code/code.bin`. Graphical and command-line
invocations retain the application's sandbox defaults. The postscript assigns
root ownership and mode 4755 to `/usr/share/code/chrome-sandbox`.

MOS supports the SUID helper's chroot and PID namespace isolation and process
dumpability controls. Private network namespaces provide independent loopback
interfaces. The SUID sandbox uses filesystem and PID namespace isolation.
User namespace creation and seccomp filtering are unsupported.

The configured desktop account uses a 60-second shell environment resolution
timeout through `application.shellEnvironmentResolutionTimeout` in
`~/.config/Code/User/settings.json`.

The desktop account configures the LLVM clangd extension to use the installed
`/usr/bin/clangd` language server, with server update checks disabled.
`C_Cpp.intelliSenseEngine` is `disabled` so Microsoft C/C++ and clangd do not
provide competing language services. Microsoft C/C++ debugging remains available.

The package launcher selects ANGLE with the OpenGL backend and enables GPU
rasterization and zero-copy rendering. It enables the Chromium features
`AcceleratedVideoDecoder`, `AcceleratedVideoDecodeLinuxGL`,
`AcceleratedVideoEncoder`, and `VaapiIgnoreDriverChecks`. GPU blocklist checks
are bypassed for the virtual GPU. The application sandbox remains enabled.
The hardware video device is `/dev/dri/renderD128`, selected explicitly with
`--hardware-video-device-path`. Video codec availability depends on the VirGL
VA-API driver and host GPU.
Additional command-line arguments are passed to the application.

The graphical and command-line launchers select V8 single-threaded garbage
collection. Garbage collection does not use parallel workers. The launchers
set `DOTNET_EnableDiagnostics=0` for the extension signature verifier;
.NET diagnostic attachment is unavailable in these processes. Marketplace
extension signature verification remains enabled.

Empty per-user extension registries are omitted from the sysroot overlay.
Installed extension registrations in the image remain available during setup.
