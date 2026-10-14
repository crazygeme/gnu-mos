# Docker on MOS

The x64 package set installs Docker Engine and its runtime from SHA-256-pinned
Debian packages. `docker` provides `docker-ce` 29.9.0,
`docker-ce-cli` provides the matching client, and `containerd.io` 2.4.1 includes
runc 1.5.2. Runtime libraries and packet-filter utilities have explicit package
dependencies. Downloads use the Tsinghua University mirrors.

`./lfs setup --arch x64` installs `/etc/docker/daemon.json`,
`/etc/init.d/docker`, and `/etc/rc3.d/S45docker`. Runlevels 3 and 5 start Docker
after network initialization. The service mounts the cgroup v1 `pids` and
`devices` hierarchies, waits for the daemon API, and validates the daemon PID
before stopping it. The log is `/var/log/docker.log`.

```sh
/etc/init.d/docker start
docker pull busybox:1.37.0
docker run --rm --network host busybox:1.37.0 echo MOS_DOCKER_OK
/etc/init.d/docker restart
```

The configuration selects the `vfs` storage driver, disables the containerd
snapshotter, and selects `io.containerd.runc.v2` with `NoPivotRoot=true`.
Root filesystem placement uses a private mount namespace, `MS_MOVE`, and
`chroot`. Bridge creation, Docker iptables rules, IP forwarding, and IP
masquerading are disabled. Containers require `--network host`; port publishing
and independent container network namespaces are unsupported. The kernel does
not provide `NETLINK_NETFILTER`; the packaged iptables and nftables utilities
cannot initialize their packet-filter backend.

MOS provides mount, UTS, PID, shared-memory IPC, and cgroup namespaces.
The `pids` controller enforces hierarchical process/thread counts; the `devices`
controller checks device opens and creation. Cgroup v2, CPU, memory, cpuset,
I/O resource controllers, user namespace creation, and network namespace
creation are unsupported. `/dev/mqueue` has an IPC-namespace filesystem root;
POSIX message queue system calls are unsupported. `oom_score_adj` records an
inherited process preference without implementing an OOM victim selector.

Seccomp filtering is unsupported; Docker runs containers without its default
seccomp profile. Capability sets and namespace/mount/device checks are present,
but some privileged operations retain UID-based checks. Device and network
subsystems are shared. The runtime does not provide the complete isolation
boundary of a Linux host.

## Validation

Run `smoke-test.sh` as root in a MOS guest with a usable image and outbound
network access when the image requires downloading. The script validates
container execution and deletion, PID 1 visibility, hostname selection,
`docker exec`, logs, device access restrictions, a process limit of 32,
bind volumes with relative symlinks, read-only mounts, and a non-root user.
`DOCKER_TEST_RESTART=1` additionally
restarts the daemon and validates execution after restart.

```sh
DOCKER_TEST_RESTART=1 sh /path/to/smoke-test.sh
```

MOS kernel probes are stored in `.workspace/sources/mos/test/`, including
`clone_namespaces.sh`, `cgroups.sh`, `capability_namespace.sh`,
`proc_fd_namespace.sh`, `realtime_signals.sh`, `subreaper.sh`,
`fifo_reopen.sh`, `bind_mounts.sh`, `wait_signals.sh`,
`shared_file_write.sh`, and `oom_score_adj.sh`.
