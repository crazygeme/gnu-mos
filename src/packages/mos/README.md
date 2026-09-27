MOS is built as a kernel package. Its userspace is not copied from any
distribution image. The package produces the generic `/boot/kernel` artifact
consumed by GRUB; all userspace files are produced by the LFS package set.

The build exports the checkout's current commit into a separate build directory
and applies package patches to that export. The source checkout is not modified.

`/proc/meminfo` reports `Cached` from physical file-cache pages and `Buffers`
from block-cache storage. Internal page-table and pathname allocation counters
are excluded from these fields. Cache values are bounded by allocated physical
memory because cache and allocator counters are sampled independently.
`MemAvailable` conservatively reports allocator-free memory; it does not include
an estimate of reclaimable cache. The `Mem:` summary uses bytes, and the named
`kB` fields use units of 1024 bytes.
