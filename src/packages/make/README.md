# GNU Make

GNU Make 4.4.1 is included in the console and desktop profiles for x86 and
x64. The cross-compilation recipe installs the target `/usr/bin/make` and
its documentation into the sysroot. Guest build recipes execute through
`/bin/sh` unless the makefile specifies another shell.

GNU Make invokes the commands declared in makefiles. Compilation additionally
requires the applicable target compiler, headers, libraries, and build tools.

```sh
make --version
make
make -j4
```
