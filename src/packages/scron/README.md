scron 0.4 installs `/usr/bin/crond` and the `scron(1)` manual.
Runlevel 3 starts the daemon through `/etc/rc3.d/S40scron`, after sysklogd.
The service supports `start`, `stop`, `restart`, `reload`, and `status` through
`/etc/init.d/scron`. Its PID file is `/var/run/crond.pid`.

`/etc/crontab` contains five time fields followed by a shell command:
minute, hour, day of month, month, and day of week. There is no username
field and no per-user crontab command. Jobs execute as root using `/bin/sh`.
Use `su -c 'command' username` to select another account. Commands should
use absolute paths and explicit output redirection. The supplied file
contains no active jobs. After editing it, run `/etc/init.d/scron reload`.
Daemon messages use syslog and are routed to `/var/log/messages`.
