MATE System Monitor 1.28.1 reads process statistics through libgtop.

The process Memory column uses private-dirty memory only when libgtop marks
`GLIBTOP_MAP_ENTRY_PRIVATE_DIRTY` as available. Otherwise, it uses resident
memory. The configured libwnck integration adds the estimated X server
resource usage to this value.

MOS exposes the 2.4.20-8 ABI and provides `/proc/<pid>/maps`; `/proc/<pid>/smaps`
is unavailable. The Memory column therefore uses resident memory and the X
server resource estimate.

The package applies `proc-map-private-dirty.patch` before configuration.
