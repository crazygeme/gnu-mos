MOS is built as a kernel package. Its userspace is not copied from any
distribution image. The package produces the generic `/boot/kernel` artifact
consumed by GRUB; all userspace files are produced by the LFS package set.

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
