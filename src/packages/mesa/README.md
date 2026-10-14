# Mesa Build and Diagnostics

Mesa 25.1.9 is cross-compiled with the VirGL Gallium driver, OpenGL, EGL,
VA-API, and the Venus Vulkan driver. All video codecs are enabled. The VA-API frontend depends
on the guest libva package. Available hardware codec profiles are supplied
by the host renderer.

The build uses native Python 3.13.7 from
`.workspace/<arch>/tools/bin/python3` for source generation. The NIR algebraic
generator reads `src/compiler/nir/nir_opt_algebraic.py` and writes
`src/compiler/nir/nir_opt_algebraic.c` in the Mesa build directory.
A generator process failure stops the Ninja build before the generated
source can be compiled.

Build output is recorded in `.workspace/<arch>/logs/mesa.log`. Python fatal
error diagnostics can be enabled through the inherited environment:

```sh
PYTHONFAULTHANDLER=1 ./lfs build --all
```

Use `--arch x86` for the 32-bit configuration. The default configuration is
x64. Fatal interpreter errors produce a Python stack trace when the fault
handler can execute. A native crash dump provides the C stack and register
state required to diagnose faults without a Python stack trace.

Vulkan uses Vulkan-Headers and Vulkan-Loader 1.4.309. The driver manifest is
installed under `/usr/share/vulkan/icd.d`, and the driver library is installed
under `/usr/lib`. Vulkan-Tools 1.4.309 provides `vulkaninfo` and `vkcube`.
The console profile excludes the Vulkan packages.

The Vulkan command path is:

```text
Vulkan application → Vulkan Loader → Mesa Venus → MOS VirtIO GPU → QEMU → host Vulkan
```

The graphical launcher enables blob resources, Venus, a 256 MiB host-visible
PCI aperture, and shared memfd guest RAM. The host requires a Vulkan driver
compatible with Venus, including external memory export. MOS supports context
capset selection, 64 command rings, guest and host blob resources, bounded
shared mappings, and PRIME handle sharing. Resource allocations are limited to
64 MiB each. Host fence descriptors become readable after synchronous host-ring
completion. Input fence descriptors, DRM syncobjs, and nonzero polling-ring
masks are unsupported.

Inside the guest, inspect the Vulkan device and display a rendered cube:

```sh
vulkaninfo --summary
vkcube
```

`tests/guest/vulkan_smoke.c` validates GPU buffer filling, fence completion,
and coherent host-visible memory. It rejects a CPU Vulkan device.

The compiler uses `-fno-strict-aliasing` for Vulkan structure chains and retains
debug information. Compiler optimization remains enabled.

H.264 encoding uses matching Mesa and virglrenderer protocol patches. The
protocol carries sequence, picture, and slice parameters together with packed
NAL headers. Each picture supports up to 32 packed headers with a combined
size of 16 KiB. Host encoding consumes the supplied headers and reference-frame
indices. Mesa and virglrenderer must be deployed together.

Classic VirGL PRIME plane imports use independent single-plane textures. Their
plane index is zero for sampler views. Blob imports retain the plane index
required by their multi-plane resource layout.

H.264 decode protocol version 1 carries complete VA-API slice parameters,
including reference lists and prediction weights. Each picture supports up to
128 slices with a 3128-byte VA-API slice structure. Mesa and the host renderer
must use matching protocol patches. The host resolves reference surfaces and
NAL data offsets and uses normal slice decoding when supported. Base slice
decoding is selected for drivers that advertise only that mode. Picture
parameters include macroblock dimensions and initialized reserved fields.
Exported video surfaces retain 64-bit DRM
modifiers, which are supplied to EGL for decoded-plane texture imports.
Decoded-surface copies preserve texture and framebuffer bindings. H.264
reference pictures are resolved across all 16 reference slots.
The host selects NV12 as the preferred format when the VA-API driver advertises
it and explicitly allocates NV12 surfaces for NV12 guest buffers. VA-API decode
targets requested as I420 or YV12 use NV12 storage when it is the driver's
preferred decode format. Image retrieval converts to the requested image
format. Guest and host decoded-plane layouts therefore agree.
Decoded planes are marked as modified by the host so that CPU mappings download
the current texture contents.

`tests/guest/browser_h264.py` verifies `VaapiVideoDecoder` selection and compares
rendered and downloaded RGB samples against software decoding of the same
fixture. Alpha values do not contribute to the pixel comparison. Use
`--loops 1` for a targeted decoder session; additional sessions validate
resource reuse when relevant.
