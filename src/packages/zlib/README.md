# zlib

zlib 1.3.1 is built as shared and static libraries with position-independent code
using `-fPIC`. The libraries and development headers are installed in the
selected architecture sysroot. `libz.so.1` supplies the runtime interface for
Debian binary packages. The static archive supports linking into shared
libraries and Python extension modules.

The zlib package precedes Python in the configured build order. Its build
version determines whether the installed libraries require recompilation.
