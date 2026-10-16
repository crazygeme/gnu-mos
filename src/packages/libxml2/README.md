# libxml2

libxml2 2.13.8 is installed for both the build host and the selected target
architecture. Both builds enable ICU encoding conversion and link directly
to the ICU internationalization and common libraries, `icu-i18n` and `icu-uc`.

The package applies `meson-icu-uc.patch` to its extracted build source before
configuration. The patch declares the common library as a direct Meson
dependency for the Unicode conversion functions used by `encoding.c`.

The package applies `meson-symbol-versions.patch` to link Linux shared
libraries with the upstream `libxml2.syms` version script. Both host and
target libraries provide the `LIBXML2_*` symbol versions required by Debian
LLVM binaries. The version script is a link dependency of the library target.

ICU 77.1 is included in both console and desktop package selections and is
built before libxml2. The host build requires the distribution's ICU development
package, declared as `libicu-dev` on APT-based hosts.
