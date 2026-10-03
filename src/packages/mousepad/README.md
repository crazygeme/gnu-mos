# Mousepad Build Requirements

The package builds Mousepad 0.6.5 with GtkSourceView 4, keyfile settings,
spell checking, and the shortcuts plugin enabled. When target Polkit support
is available, Meson generates and installs `org.xfce.mousepad.policy` through
the native host `msgfmt` tool.

Policy translation requires the Polkit ITS rules on the host. On Debian and
Ubuntu, `gettext` provides `msgfmt` and `libpolkit-gobject-1-dev` provides
`/usr/share/gettext/its/polkit.its` and
`/usr/share/gettext/its/polkit.loc`. Target Polkit libraries in the sysroot
do not supply these rules to the native host translation tool.

Both host packages are declared in `host-packages.apt`. Before source
preparation, `./lfs build` installs missing packages through
`apt-get install --yes`, using `sudo` when required. Installed dependencies
do not trigger installation. Installation failure stops the build before
configuration and compilation.

The equivalent manual installation command is:

```sh
sudo apt install gettext libpolkit-gobject-1-dev
```
