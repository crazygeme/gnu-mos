# Host Python

Python 3.13.7 is installed in the selected architecture's tools prefix and
runs Meson and other build utilities on the host. Native development packages
`libbz2-dev`, `liblzma-dev`, and `zlib1g-dev` provide the `_bz2`, `_lzma`, and
`zlib` modules required for compressed source archives.

These dependencies are declared through `host-packages.apt` and are installed
before host Python configuration on APT-based hosts.
