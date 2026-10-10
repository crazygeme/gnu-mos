# Microsoft Edge

The package installs Microsoft Edge 154.0.4258.62-1 for x64 GUI images.
`/usr/bin/microsoft-edge` and `/usr/bin/microsoft-edge-stable` invoke the
application launcher in `/opt/microsoft/msedge`.

The package postscript retains the vendor launcher as `microsoft-edge.vendor`
and installs a launcher that supplies `--no-sandbox`. MOS does not implement
Chromium namespace and seccomp isolation. Edge processes therefore run without
Chromium sandbox protection. The SUID helper has root ownership and mode 4755.
