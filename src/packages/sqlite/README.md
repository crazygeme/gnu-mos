# SQLite

SQLite 3.46.1 is installed as a static library in the selected architecture
sysroot. Configuration enables `--with-pic` so the archive contains
position-independent code suitable for shared-library consumers.

SQLite precedes util-linux in the configured build order. The util-linux
`liblastlog2` shared library links against the SQLite archive.
