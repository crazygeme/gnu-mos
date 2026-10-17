# Microsoft Edge

The package installs Microsoft Edge 154.0.4258.62-1 for x64 GUI images.
`/usr/bin/microsoft-edge` and `/usr/bin/microsoft-edge-stable` invoke the
application launcher in `/opt/microsoft/msedge`.

The package postscript retains the vendor launcher as `microsoft-edge.vendor`
and installs a launcher that retains the application's sandbox defaults.
The SUID helper has root ownership and mode 4755.

MOS supports the SUID helper's chroot and PID namespace isolation and process
dumpability controls. Private network namespaces provide independent loopback
interfaces. The SUID sandbox uses filesystem and PID namespace isolation.
User namespace creation and seccomp filtering are unsupported.

The package launcher selects ANGLE with the OpenGL backend and enables GPU
rasterization and zero-copy rendering. It enables the Chromium features
`AcceleratedVideoDecoder`, `AcceleratedVideoDecodeLinuxGL`,
`AcceleratedVideoEncoder`, and `VaapiIgnoreDriverChecks`. GPU blocklist checks
are bypassed for the virtual GPU. The application sandbox remains enabled.
The hardware video device is `/dev/dri/renderD128`, selected explicitly with
`--hardware-video-device-path`. Video codec availability depends on the VirGL
VA-API driver and host GPU.
Additional command-line arguments are passed to the application.
