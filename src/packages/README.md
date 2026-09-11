# Package Layout

Each package directory contains a `package.json` manifest and a `build.py`
recipe.

`source=archive` requires `url` and `archive`. The fetch stage downloads the
archive into `.workspace/sources/` and the build recipe consumes that file.

`source=git` requires `git`. The fetch stage clones the selected branch into
`.workspace/sources/<name>/` and the build recipe consumes that checkout.

`source=meta` identifies a package that creates system integration files or
coordinates components without downloading a standalone source archive. It is
not used as a substitute for missing source packages.

Every compiled userspace component must have its own manifest and build recipe.
The package list is intentionally explicit so each download, version, build
order, and artifact is inspectable.
