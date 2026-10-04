# GNU M4

The package builds GNU M4 1.4.19 as a native host tool and installs it into
`.workspace/<arch>/tools`.

The source archive is downloaded from
<https://mirrors.ustc.edu.cn/gnu/m4/m4-1.4.19.tar.xz>.
The corresponding upstream archive is available at
<https://ftp.gnu.org/gnu/m4/m4-1.4.19.tar.xz>.
Both archives have the SHA-256 digest
`63aede5c6d33b6d9b13511cd0be2cac046f2e70fd0a07aa9573a04a82783af96`.

`./lfs build --all` downloads missing source archives and builds pending packages
in manifest order. Downloads use a temporary file that is renamed only after
successful transfer; an unsuccessful transfer removes the temporary file.
