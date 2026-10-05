MOS is built as a kernel package. Its userspace is not copied from any
distribution image. The package produces the generic `/boot/kernel` artifact
consumed by GRUB; all userspace files are produced by the LFS package set.

IPC circular buffers use contiguous copies across wrap boundaries. Pipe data
notifications publish data and readiness before returning, and wake waiters
without an immediate scheduler yield. Unix stream
sockets allocate 256 KiB receive rings per endpoint; datagram receive rings
allocate 4 KiB. Socket waits without a timeout do not sample the hardware clock.
Unix socket I/O retains preemption protection and skips lwIP timer refreshes.
Unix stream rings do not sample the packet timestamp clock, and `SIOCGSTAMP`
returns `ENOTTY` for Unix stream sockets.
`test/ipc_buffers.py` checks stream integrity, readiness, shutdown, datagram
truncation, finite timeouts, and descriptor passing inside a MOS guest.
[IPC performance](../../../docs/ipc-performance.md) defines benchmark modes,
operation counts, and measurement procedures.

The build copies tracked and non-ignored untracked files from the MOS working
tree into a separate build directory, including uncommitted source edits.
Compilation uses this copy and leaves the source working tree unchanged.

`prctl` supports `PR_SET_PDEATHSIG` and `PR_GET_PDEATHSIG` for the kernel's
supported signal range. Parent exit queues the configured signal and wakes
eligible recipients. Fork and clone clear the child's setting; effective or
filesystem credential changes and privileged executable images clear it.

`/proc/meminfo` reports `Cached` from physical file-cache pages and `Buffers`
from block-cache storage. Internal page-table and pathname allocation counters
are excluded from these fields. Cache values are bounded by allocated physical
memory because cache and allocator counters are sampled independently.
`MemAvailable` conservatively reports allocator-free memory; it does not include
an estimate of reclaimable cache. The `Mem:` summary uses bytes, and the named
`kB` fields use units of 1024 bytes.

Numeric entries in `/proc` report `DT_DIR` through `getdents64` and native
`getdents`. Per-process regular files and directories retain the effective UID
and GID of the process at open time. These interfaces support libgtop process
enumeration and the MATE System Monitor process ownership filter.
PID 1 has parent PID 0, as reported by `getppid()`, `/proc/1/status`, and
`/proc/1/stat`.
Per-process virtual memory totals count mapped regions once. Resident totals
count physical pages mapped within those regions; direct physical device
mappings are excluded. Stack accounting uses each process's userspace address
limit. `/proc/<pid>/stat`, `status`, and `statm` share 64-bit memory counters.
The `statm` shared field reports resident pages in file-backed regions.
`test/proc_memory.py` checks virtual size and residency across an anonymous
reservation, page writes, and unmap, including agreement between the three
per-process memory interfaces.
`test/proc_processes.py` checks directory-entry types, ownership, parent
identifiers, and libgtop process selection inside a MOS guest with libgtop
installed.

The VirtIO-GPU DRM connector represents scanout zero. The driver queries
`VIRTIO_GPU_CMD_GET_DISPLAY_INFO` during initialization and on explicit
connector probes by the DRM master. The reported dimensions become the
preferred resolution. Missing, disabled, or out-of-range display information
selects a 1024 × 768 fallback. A failed runtime probe returns an error and
preserves the cached mode list.

The connector provides the preferred resolution and common resolutions from
640 × 480 through 3840 × 2160 with nominal 60 Hz and 120 Hz timings. The
preferred mode uses 120 Hz. These virtual timings do not guarantee a
presentation rate. EDID data and physical monitor dimensions are not exposed.

Legacy DRM modesetting accepts valid progressive modes up to 4096 pixels per
axis, including custom modes. The selected mode and framebuffer offset define
the scanout rectangle, which must fit entirely within the framebuffer.
`GETCRTC` reports the committed mode, framebuffer, and offset. Invalid mode
or viewport requests preserve the current scanout. Mode state is committed
after the device accepts `SET_SCANOUT`. Disabling the CRTC clears its state.
The driver does not emit display hotplug notifications; host display changes
require an explicit connector probe and userspace mode selection. Changing
resolution through the Xfce display settings does not require a kernel rebuild.

`test/virtgpu_modes.py` checks connector enumeration, mode timings, and bounded
mode-array copies inside a MOS guest. `--expect-preferred WIDTHxHEIGHT` checks
the dimensions supplied by the host. With Xorg stopped, running the script as
root with `--modeset` also checks repeated mode changes, framebuffer offsets,
custom modes, invalid requests, and CRTC disable state. The modesetting checks
require an initially disabled CRTC and leave it disabled.

The text console supports basic and bright ANSI colors, indexed 256-color
SGR sequences, semicolon-separated RGB colors, and reverse video. The tmux
configuration declares indexed color capabilities for the `linux` terminal
and disables unsupported console erase and alternate-character-set features.

The text console renders byte-indexed VGA glyphs and does not decode UTF-8.
UTF-8 locales do not provide Unicode rendering in this console. Xterm is built
with wide-character and FreeType support and uses the `C.UTF-8` locale;
Unicode display requires fonts containing the requested glyphs. SSH display
uses the client terminal's Unicode and font support.

PTY window-size changes notify the foreground process group with `SIGWINCH`.
Repeated `TIOCSWINSZ` requests with identical dimensions do not generate a
notification. Text-console geometry changes also notify the foreground
process group after resizing the saved cell buffers. `test/pty_winsize.py`
checks PTY size propagation and foreground-group notifications.

`/proc/<pid>/cwd` and `/proc/self/cwd` expose the process working directory
as symbolic links. Each lookup reflects the current directory, and `readlink`
returns at most the supplied buffer length without a trailing null byte.
Tmux uses the foreground process's link to populate `pane_current_path`,
including the path displayed in window labels.

The selected `--arch x86|x64` value is passed to the kernel build as `ARCH`.
Build snapshots reside under `.workspace/<arch>/build/mos`. The x86 package
installs `out/x86/release/kernel`; the x64 package installs
`out/x64/release/kernel.boot`. Both are installed as `/boot/kernel` for
BIOS GRUB Multiboot loading. The source checkout is shared between architectures.

The x86 kernel accepts ELF32 images with machine type `EM_386`. The x64
kernel accepts both ELF32/i386 and ELF64/AMD64 images. Executables and their
interpreters must use the same ELF class. ELF preparation selects a format
with header readers, a typed initial-stack builder, register initialization,
and explicit address-space limits. Fork and clone preserve the user execution
context and VM limits.

Each syscall namespace selects its own wire adapters. Ptrace register and
memory words, shared-memory metadata, and socket timestamps are serialized
by the caller's adapter. Robust-list registration installs a typed list reader
and records the registered head size. Cleanup uses that reader independently
of subsequent syscall entry. Signal delivery and clone TLS interpretation
use the saved code selector within the architecture backend.

Page execute permissions follow the paging architecture. The x64 kernel
enforces `PROT_EXEC` with NX page-table bits for both i386 and AMD64 processes.
The x86 backend uses non-PAE page tables without NX support.

Native AMD64 `newfstatat` preserves the pathname lookup flags, including
`AT_SYMLINK_NOFOLLOW` and `AT_EMPTY_PATH`. Native `select` and `pselect6`
convert 64-bit time fields and descriptor-set words to the shared wait service.
They support readiness notifications, finite timeouts, and interrupted waits.
`pselect6` accepts an eight-byte signal mask and prevents blocking `SIGKILL`
and `SIGSTOP`. Timeout seconds must fit a nonnegative signed 32-bit value;
finite waits use millisecond resolution. Native `clock_nanosleep` supports
relative and absolute waits for `CLOCK_REALTIME` and `CLOCK_MONOTONIC`.

Native AMD64 `ftruncate` supports sizing shared-fence files for DRI3 rendering.
The console ABI test checks truncation and shared mapping visibility for an
unlinked file. The Bochs text console renders and scrolls in a RAM shadow,
then copies the accumulated dirty pixel range to video memory per write.

Native `ppoll` converts 64-bit timeouts to the shared poll wait service.
`ppoll` and `pselect6` retain their temporary masks through signal delivery
when interrupted and restore the original masks on signal return.

`test/x64_console_abi.py` in the MOS source tree checks native pathname flags,
descriptor readiness across word boundaries, timeout writeback, signal
interruption, and libc sleep calls. It runs inside an AMD64 guest with Python 3.

Native socket calls support binding, connection, listening, address queries,
socket options, datagram I/O, shutdown, and socket pairs through the shared
network services. Socket-pair creation and `accept4` preserve nonblocking and
close-on-exec flags. The console ABI test also checks Unix-domain datagrams,
IPv4 socket binding and options, stream socket pairs, and accepted descriptors.

Native futex calls use the shared 64-bit timeout reader with the original
userspace address. Relative and absolute timed waits preserve the AMD64
timespec layout. The console ABI test checks both timeout modes.
The network startup service checks the default lwIP interface, `e01`.

The VirtIO GPU probe validates physical PCI BAR ranges against the
architecture's device I/O window. On x64, this window spans `0xc0000000`
through `0x100000000`, independently of the high kernel virtual I/O range.

Virtual-terminal shell tasks set the privilege-entry stack to the full-width
task address plus `KERNEL_TASK_BYTES`.
Terminal hotkeys create shells on the selected text terminal. A terminal
owned by a graphics session does not create a shell during activation.

MOS provides `epoll_create`, `epoll_create1`, `epoll_ctl`, `epoll_wait`,
`epoll_pwait`, and `epoll_pwait2` for i386 and AMD64. Persistent subscriptions
and a ready queue avoid scanning idle interests during waits. Level and edge
delivery, one-shot rearming, duplicate descriptor lifetime, signal masks, and
bounded nesting are supported. The sysroot installs `posix_epoll.sh` in `/root`
and `/home/ezheng` for manual interface and libevent backend validation with
the configured LFS userspace toolchain. The script builds its probe under
`${HOME}/tests/posix_epoll` and is excluded from the embedded kernel script
suite. `test/epoll_qemu.py` runs isolated guest validation and compares syscall
timings against Linux. The libevent and Xorg package configurations select
their epoll backends.
