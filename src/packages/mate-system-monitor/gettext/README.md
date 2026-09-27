# PolicyKit translation rules

The `its/polkit.its` and `its/polkit.loc` files are provided by
[polkit 126](https://github.com/polkit-org/polkit/tree/126/gettext/its).
These rules select action descriptions and authentication messages for
translation in PolicyKit policy XML files.

The package build sets `GETTEXTDATADIRS` to include this directory so that
gettext can generate the translated application policy.
