GNU Screen 5.0.1 installs `/usr/bin/screen` and uses `/etc/screenrc`.
It links against ncurses, libxcrypt, and Linux-PAM. The binary runs without
set-user-ID; PAM uses `/etc/pam.d/screen` for authentication.
The MOS console configuration uses ASCII line drawing and terminal
capabilities compatible with `TERM=linux`.

Run `screen` to start a session, `screen -ls` to list sessions, and
`screen -r` to resume one. The default command prefix is Ctrl-a;
Ctrl-a d detaches the session.
