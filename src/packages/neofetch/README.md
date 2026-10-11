# Neofetch

Neofetch 7.1.0 provides the `neofetch` system information command in the
console and GUI profiles for x86 and x64. The package installs the Bash
script into `/usr/bin/neofetch`, the manual page into
`/usr/share/man/man1/neofetch.1`, and the MIT license into
`/usr/share/licenses/neofetch/LICENSE.md`. Installation does not require
compilation.

The manifest declares Bash and the target command-line utilities used to
collect system information. The source archive is verified with SHA256.
The `mos-kernel.patch` patch recognizes the `MOS` kernel identity, selects
the Linux-compatible information collectors, and displays `MOS` as the
operating system name.
Automatic ASCII selection displays the MOS logo. Unsupported ASCII names
fall back to the MOS logo on the MOS kernel. Distribution output includes
the machine architecture when `os_arch` is enabled.
Terminal detection reads the process name from `/proc/<pid>/status` when
`/proc/<pid>/comm` is unavailable. Parent traversal stops at PID zero or a
repeated PID. If no terminal is identified, the terminal field uses `TERM`
or `unknown` when `TERM` is unset.

```sh
neofetch
neofetch --off
man neofetch
```

`neofetch --off` displays information without an image or ASCII logo.
User configuration resides in
`${XDG_CONFIG_HOME:-$HOME/.config}/neofetch/config.conf`.
Available fields depend on the kernel interfaces, system files, and optional
utilities present in the target system.
