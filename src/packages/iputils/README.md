# iputils Build Requirements

The package builds iputils 20250605 with ping, tracepath, and manual-page
generation enabled. Manual pages are generated from DocBook XML through the
native host `xsltproc` executable and the namespaced DocBook XSL stylesheets.

On Debian and Ubuntu, the package declares `xsltproc` and `docbook-xsl-ns`
in `host-packages.apt`. Before source preparation, `./lfs build` installs
missing host packages through `apt-get install --yes`, using `sudo` when
required. Installed dependencies do not trigger installation. Installation
failure stops the build before configuration and compilation.

The equivalent manual installation command is:

```sh
sudo apt install xsltproc docbook-xsl-ns
```

The stylesheets resolve the
`http://docbook.sourceforge.net/release/xsl-ns/current/` imports through the
host XML catalog. iputils invokes `xsltproc` with `--nonet`, so documentation
generation requires locally installed stylesheets.
