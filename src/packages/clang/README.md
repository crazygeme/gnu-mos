# Clang C and C++ Toolchain

The `clang` and `clang-tools` packages import Debian 13 amd64 binaries for
LLVM/Clang 19.1.7 (`1:19.1.7-3+b1`). Both packages are selected for `x64`
console and GUI builds. The `x86` build excludes these packages and their
Debian binary dependencies.

Each Debian archive has a separate manifest, an exact version, and a SHA256
checksum. Downloads use the USTC Debian mirror. The dependency declarations
and package order include LLVM, Clang libraries, Z3, Zstandard, libedit,
Abseil, c-ares, RE2, Protobuf, and gRPC. Existing source packages supply glibc,
GCC runtime and development files, binutils, libffi, libxml2, OpenSSL,
ncurses, libbsd, zlib, Python, and Perl.

`./lfs setup --arch x64` runs the package postscripts. The Clang postscript
provides `clang`, `clang++`, and `clang-cpp` aliases and configures the
`x86_64-lfs-linux-gnu` target with the GCC 15.2.0 installation under
`/usr/lib/gcc/x86_64-lfs-linux-gnu/15.2.0`. The supported compiler configuration
uses the system C headers and GCC C++ headers, libstdc++, and libgcc.
Objective-C development files are not included.

The `libc++-dev` and `libc++abi-dev` packages import Debian's
`libc++-19-dev` and `libc++abi-19-dev` archives at version `1:19.1.7-3+b1`.
They are dependencies of `clang` and are selected for `x64` console and GUI
builds. Separate manifests supply `libc++1-19`, `libc++abi1-19`,
`libunwind-19`, and `libunwind-19-dev` in dependency order.

libc++ headers are available under `/usr/include/c++/v1`, with ABI headers
under `/usr/lib/llvm-19/include/c++/v1`. Libraries and static archives reside
under `/usr/lib/llvm-19/lib`, with Debian multiarch aliases and shared-library
aliases in `/usr/lib`. Select libc++ explicitly when compiling and linking:

```sh
clang++ -stdlib=libc++ main.cpp -o main
```

The `libc++.so` linker script selects libc++, libc++abi, and LLVM libunwind.

The `clang-tools` package includes the separate `clang-format` and `clangd`
Debian packages as dependencies. Its postscript exposes the installed LLVM
tool directory commands in `/usr/bin`, including `clang-format`, `clangd`,
`clang-check`, `clang-query`, `clang-scan-deps`, `clang-apply-replacements`,
and `scan-build`. Debian versioned command names remain available.

Debian shared libraries retain their `/usr/lib/x86_64-linux-gnu` paths.
The Clang postscript creates relative library aliases in `/usr/lib` where
no entry exists, allowing the system loader to resolve these dependencies.
Debian maintainer scripts and package-manager triggers are not executed.
Successful archive extraction does not certify execution on MOS.
