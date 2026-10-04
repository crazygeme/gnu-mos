# Git Build Requirements

The package builds Git 2.51.0 for the selected x86 or x64 target. Git's Makefile uses the
native host `msgfmt` tool to compile translation catalogs from `po/*.po`
into `po/build/locale/*/LC_MESSAGES/git.mo` when catalog generation is enabled.

On Debian and Ubuntu, the `gettext` distribution package provides `msgfmt`.
The package declares this dependency in `host-packages.apt`. Before source
preparation, `./lfs build` installs the package if it is missing through
`apt-get install --yes`, using `sudo` when required. An installed dependency
does not trigger installation. Installation failure stops the build before
configuration and compilation.

The equivalent manual installation command is:

```sh
sudo apt install gettext
```
