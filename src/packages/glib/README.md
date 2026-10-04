# GLib

GLib 2.88.1 uses the target `libpcre2-8` installed by the PCRE2 package.
PCRE2 precedes GLib in both console and desktop package selections.

Configuration uses Meson's `nofallback` wrap mode for dependency resolution.
Dependency libraries must be installed in the selected architecture sysroot;
automatic dependency fallback builds are not selected.
