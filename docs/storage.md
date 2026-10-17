# Fixed block storage

The LFS system image is attached as a PCIe NVMe namespace. The configured
root volume is `/dev/nvme0n1p1`, and `/etc/fstab` identifies this volume.
The kernel selects its root filesystem by probing discovered volumes.
Device names and storage bus enumeration order do not identify a filesystem.

MOS provides PCI IDE, SATA AHCI, and PCIe NVMe NVM command-set drivers.
The fixed-storage layer publishes whole disks and partitions through the
block subsystem, `/dev`, and sysfs. IDE disks use `hda`, `hdb`, and subsequent
letters; their partitions use `hda1` and subsequent numbers. AHCI disks use
`sata0` and partitions such as `sata0p1`. NVMe namespace identifiers appear
in names such as `nvme0n1`; partitions use `nvme0n1p1`.

MBR primary partitions, bounded extended-partition chains, and GPT primary
headers and entry arrays are supported. GPT header and entry-array CRC32
values are validated. Partition ranges must remain inside their parent disk.
Each fixed disk exposes at most fifteen partitions. An unpartitioned disk
is a filesystem candidate. The fixed-storage layer supports sixteen disks;
the block registry capacity also limits the number of published devices.

Filesystem drivers provide read-only probes through the filesystem registry.
The ext filesystem probe validates the superblock, its checksum, logical
block size, filesystem capacity, and supported incompatible features.
Volume lookup performs this probe for IDE, AHCI, NVMe, USB, and loop devices.
Root discovery attempts a read-only mount of each recognized volume until a
mount succeeds. Blank volumes, unreadable volumes, unsupported formats, and
failed mounts do not terminate discovery. Read/write root remounting uses
the mounted root device.

All fixed disks share a bounded write-back cache with sixty-four 32 KiB
extents per disk. A disk mutex serializes cache access and partial-sector
read/modify/write operations across whole-disk and partition nodes. Dirty
extents are written before eviction. Flush operations write dirty extents
and issue the transport cache-flush command. Failed writes retain dirty
cache state. Discard flushes cached writes before issuing the transport
command and invalidates cached extents after success.

The NVMe driver initializes the controller, admin queue, and one I/O queue
pair, enumerates active namespaces, and identifies native LBA formats.
Transfers use page-aligned DMA bounce buffers and PRP lists, bounded by the
controller's maximum transfer size. Namespace read, write, flush, and optional
Dataset Management deallocation are supported. Logical sector sizes of
512, 1024, 2048, and 4096 bytes are accepted without metadata or protection
information. Completion polling validates phase, command ID, queue ID, and
status. A fatal status or timeout disables the controller and bus mastering;
subsequent requests fail. Shutdown flushes disks, requests normal NVMe
shutdown, and disables the controller.

The AHCI driver performs BIOS handoff when advertised, initializes command
and received-FIS DMA memory, and uses serialized READ/WRITE DMA commands.
LBA48 commands and native logical sectors are supported when advertised;
LBA28 DMA commands are available for compatible disks. ATA cache flush and
optional Data Set Management TRIM are supported. Command errors and timeouts
stop further port requests. Shutdown stops command and FIS reception engines.

Controller completion handling uses polling. Runtime controller hotplug,
NVMe namespace-management operations, metadata-bearing LBA formats, zoned
command sets, and automatic recovery after a fatal transport error are not
implemented. PCI MMIO resources must be within the architecture's supported
I/O mapping range. The QEMU launcher configures PCI resources below 4 GiB.

## Validation

`tests/guest/fixed_storage.c` performs destructive validation only on
explicitly supplied disposable block devices:

```sh
cc -O2 -Wall -Werror tests/guest/fixed_storage.c -o fixed_storage
sudo ./fixed_storage --destructive /dev/nvme1n1p1 /dev/sata0p1
```

The validation covers capacity queries, logical-sector sizes, nonaligned
transfers spanning multiple DMA buffers, concurrent writers, readback,
last-sector access, flush, discard, and invalid discard ranges. IDE reports
an unsupported discard operation. The command must not target mounted or
persistent data volumes.

MOS native validation commands are:

```sh
python3 .workspace/sources/mos/tools/tests/ata_block_io.py
python3 .workspace/sources/mos/tools/tests/fixed_cache_io.py
```

`tests/guest/browser_storage.py --port 19222 --close` checks a graphical Edge
instance through a loopback SSH tunnel to its DevTools endpoint. It validates
a trusted HTTPS page, JavaScript evaluation, Canvas pixel readback, PNG
encoding, and normal browser closure. Repeating this command after launching
the browser again validates restart behavior. Edge requires a nondefault data
directory for remote debugging. The default user profile can be validated
through VNC without remote debugging.
