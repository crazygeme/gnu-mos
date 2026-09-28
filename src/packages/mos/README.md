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
