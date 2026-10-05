# IPC Performance

## Kernel data paths

Anonymous pipes allocate 64 KiB circular buffers. Unix stream sockets allocate
256 KiB receive rings per endpoint, with one byte reserved to distinguish full
and empty states. Unix datagram sockets allocate 4 KiB receive rings. Copies
across ring boundaries use at most two contiguous memory transfers.

`cond_notify` publishes its event and makes one waiting task runnable without
switching tasks. Explicit scheduler handoffs occur after associated state has
been published. Circular-buffer notifications publish data and readiness and
make waiting tasks runnable without an immediate scheduler handoff. Blocking I/O yields when the
requested buffer state is unavailable. Input notifications remain active when
data is already buffered, preserving edge-triggered readiness delivery.

Unix socket I/O retains scheduler preemption protection and skips lwIP service
and timer refreshes. Internet socket I/O refreshes lwIP service deadlines.
Socket waits with no configured timeout do not sample the hardware clock.
Configured send and receive timeouts retain their deadline checks. AMD64
syscall adapters convert native 64-bit timeout fields to the shared timeval
layout. Timeout values are rounded up to milliseconds and bounded to
4,294,967,295 milliseconds. Timeout queries return the calling ABI layout.

Unix stream sockets do not record packet timestamps. `SIOCGSTAMP` returns
`ENOTTY` for these sockets. Unix datagram and Internet receive rings retain
packet timestamp recording.

## Benchmark programs

`src/sysroot/home/ezheng/pipe_perf.c` and
`src/sysroot/home/ezheng/unix_socket_perf.c` use separate sender and receiver
processes. Corresponding source files are also present in the MOS guest tool
directory. Both programs support GNU userspace and Red Hat 9 libc interfaces.

```sh
gcc -O2 -Wall -W -o pipe_perf pipe_perf.c
gcc -O2 -Wall -W -o unix_socket_perf unix_socket_perf.c
./pipe_perf
./unix_socket_perf
```

The default invocation runs three repetitions of each measurement:

| Mode | Default workload | Termination condition |
| --- | --- | --- |
| `throughput` | 65,536-byte chunks | At least two seconds and 16 MiB transferred |
| `latency` | 64-byte requests and replies | 10,000 measured round trips |
| `operations` | 64-byte chunks | At least one second |

`--benchmark all|throughput|latency|operations` selects the measurement mode.
`--ops-chunk N` sets the operation-rate chunk size from 1 through 1,048,576
bytes. `--ops-seconds N` sets its minimum duration. Timing is checked every 256
chunks, so execution can exceed this duration by a transfer batch and the final
receiver acknowledgement.

```sh
./pipe_perf --benchmark operations --ops-chunk 64 --ops-seconds 1
./unix_socket_perf --benchmark operations --ops-chunk 64 --ops-seconds 1
```

The socket benchmark supports `--transport pair|named|both`. The default tests
both `socketpair` and pathname-based connections. Pathname sockets are unlinked
after acceptance and before listener closure.

## Result interpretation

Output is CSV. `write_ops` counts successful sender `write()` calls made during
the measured workload. Positive partial writes count individually; interrupted
and failed calls do not count. Allocation, connection establishment, warmup,
and receiver acknowledgement writes are excluded. Receiver reads are excluded
from the operation count. `ops_per_s` divides this count by the measured elapsed
time. These fields are present in every measurement mode.

Throughput and operations intervals include draining all transmitted data and
receiving the final acknowledgement. Latency reports complete request/reply
round trips; `mean_rtt_us` is the mean round-trip time. Rates use actual elapsed
time. MB and MiB represent 1,000,000 and 1,048,576 bytes, respectively.

Timing uses `gettimeofday`. Wall-clock adjustments, guest scheduling, host
scheduling, and syscall logging affect measurements. Short latency samples can
fall below effective guest timer resolution; increasing `--roundtrips` provides
a longer measurement interval. A nonpositive elapsed time produces an error.
Timeouts terminate the benchmark with nonzero status.

Comparisons require the same binaries, payload sizes, CPU count, acceleration,
and logging configuration. Single-CPU and multiple-CPU measurements represent
different scheduling and synchronization costs.

## Two-CPU measurements

The measurement configuration uses QEMU KVM acceleration, `-cpu host`,
`-smp 2`, and 512 MiB RAM on an AMD Ryzen 9 7950X host. Both kernels execute
the same statically linked AMD64 binaries built with GCC 15.2.0 and glibc 2.42.
MOS uses package build version 44 with syscall logging disabled. The Linux
comparison uses kernel 7.0.0-38-generic. Transport buffers use each kernel's
default capacities. The measurement date is 2026-10-05.

Values are medians of three samples. Throughput uses 65,536-byte chunks and
at least two seconds per sample. Operation rate uses 64-byte chunks and at
least one second per sample. GB represents 1,000,000,000 bytes.

| Transport | MOS GB/s | Linux GB/s | MOS million ops/s | Linux million ops/s |
| --- | ---: | ---: | ---: | ---: |
| Pipe | 6.89 | 6.95 | 2.58 | 2.58 |
| Socket pair | 14.20 | 12.37 | 2.33 | 1.51 |
| Named socket | 14.48 | 12.35 | 2.34 | 1.50 |

[Complete samples](ipc-performance-results.csv) contain transferred bytes,
write counts, elapsed times, and round-trip latency measurements.

Two-CPU x86 and AMD64 guest validation covers circular-buffer, lock, and string
unit tests; fragmented pipe, FIFO, and Unix stream transfers; edge-triggered
readiness; shutdown; descriptor passing; datagram truncation; finite socket
timeouts; and vfork completion through exit and exec. Native socket timeout
regressions are defined in `test/x64_console_abi.py` in the MOS source tree.
