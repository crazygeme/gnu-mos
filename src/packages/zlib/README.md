# zlib

zlib 1.3.1 is built as a static library with position-independent code
using `-fPIC`. The archive is installed in the selected architecture sysroot
and supports linking into shared libraries and Python extension modules.

The zlib package precedes Python in the configured build order. Its build
version determines whether the installed archive requires recompilation.
