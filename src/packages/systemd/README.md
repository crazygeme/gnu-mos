# System and session services

The package builds systemd 252.39 with PAM support and the legacy cgroup
hierarchy. `/usr/sbin/init` starts systemd as PID 1. The default target is
`graphical.target`; `LFS_NO_GUI=1` selects `multi-user.target` during setup.

Native units manage D-Bus, OpenSSH, cron, Docker, and XDM. Systemd starts
journald, udev, logind, and the per-user service manager. The `systemd-user`
PAM session configures the user runtime directory and service environment.
The `mos-system-ownership.service` unit configures privileged executables
and runtime directory permissions before system initialization completes.

```sh
systemctl --failed
systemctl status xdm.service
systemctl restart sshd.service
journalctl -b
systemctl poweroff
```

MOS exposes cgroup v1 `pids`, `devices`, and `name=systemd` hierarchies.
Directory and membership-file ownership support delegated user subtrees.
Mount propagation and mount, UTS, IPC, PID, network, and cgroup namespaces
provide the interfaces used by service isolation. A private network namespace
contains an independent loopback interface; physical interfaces remain in the
initial namespace. User namespaces, seccomp filtering, cgroup v2, and CPU and
memory resource controllers are unsupported.

Polkit uses D-Bus activation and a `Type=dbus` service with its configured
filesystem and private-network isolation. Package patches are applied to the
configured Polkit source archive during its build.
