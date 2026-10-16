# ncurses

ncurses 6.5 supplies narrow-character and wide-character libraries for both
target architectures. The narrow-character build provides the separate
`libtinfo.so.6` terminfo library. The wide-character build enables
`--enable-widec`.

Both builds enable `--with-shared` and `--with-versioned-syms`. The upstream
symbol maps provide ABI 6 symbol versions, including the
`NCURSES6_TINFO_*` versions required by Debian libedit binaries.
