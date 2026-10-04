# System logging

Sysklogd 2.7.2 provides the system logging daemon. The startup handshake
installs the readiness signal handler and arms its timeout before creating
the daemon process. Alarm timers are not inherited by the daemon process.
The daemon writes its process identifier to `/run/syslogd.pid` and listens
on the Unix-domain socket `/dev/log`.
