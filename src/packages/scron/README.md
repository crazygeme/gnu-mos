scron 0.4 installs `/usr/bin/crond` and the `scron(1)` manual.
The multi-user target starts the daemon through `scron.service`.
The service supports `start`, `stop`, `restart`, `reload`, and `status` through
`systemctl ACTION scron`. Its PID file is `/run/crond.pid`.

`/etc/crontab` contains five time fields followed by a shell command:
minute, hour, day of month, month, and day of week. There is no username
field and no per-user crontab command. Jobs execute as root using `/bin/sh`.
Use `su -c 'command' username` to select another account. Commands should
use absolute paths and explicit output redirection. The supplied file
contains no active jobs. After editing it, run `systemctl reload scron`.
Daemon messages use syslog and are available through `journalctl`.
