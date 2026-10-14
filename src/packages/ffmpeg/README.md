# FFmpeg Video Acceleration

The graphical profile builds FFmpeg 8.0.3 with DRM, VA-API, Vulkan, libplacebo 7.349.0, and glslang 15.1.0 support.
Libva 2.22.0 provides the guest VA-API interface. Mesa 25.1.9 builds the VirGL
VA-API driver with all video codecs enabled. The driver is installed as
`/usr/lib/dri/virtio_gpu_drv_video.so` and is selected from the DRM device name.
The console profile builds software codecs without DRM, VA-API, or Vulkan dependencies.

The video command path is:

```text
FFmpeg → libva → Mesa VirGL → MOS VirtIO GPU → QEMU → virglrenderer → host VA-API
```

The graphical host stack uses QEMU 10.2.1 and virglrenderer 1.3.0 with video
support. The launcher selects `/dev/dri/renderD128` on the host.
`MOS_VIDEO_RENDER_NODE` selects another host render node. The host requires
a VA-API driver with DRM PRIME surface export and permission to access the selected device.
Intel iHD and AMD Mesa Gallium use the same surface-export capability check.
The available codec profiles and encoding capabilities depend on the host
GPU and driver. Build-time codec enablement does not guarantee host support.

Build pending packages for the selected architecture:

```sh
./lfs build --arch x64 --all
```

The x86 configuration uses `--arch x86`. Deployment uses the standard
`./lfs setup` workflow. Setup copies the configured sysroot into the image. New images and console
images receive a formatted ext3 partition; existing graphical images retain
their filesystem.

Inside the guest, list compiled acceleration methods and encoders:

```sh
ffmpeg -hide_banner -hwaccels
ffmpeg -hide_banner -encoders
```

These lists describe compiled interfaces. A successful device initialization
and codec operation are required to verify hardware acceleration.

Decode an 8-bit H.264 4:2:0 file through VA-API and download decoded frames:

```sh
ffmpeg -hide_banner -loglevel verbose \
    -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 \
    -hwaccel_output_format vaapi -i input.mp4 \
    -vf 'hwdownload,format=nv12' -an -f null -
```

The explicit VA-API output format and hardware download filter require
hardware frames. Software decoding cannot satisfy this filter chain.

Encode a generated sequence with the host H.264 encoder:

```sh
ffmpeg -hide_banner -loglevel verbose \
    -vaapi_device /dev/dri/renderD128 \
    -f lavfi -i 'testsrc2=size=1280x720:rate=30' -t 2 \
    -vf 'format=nv12,hwupload' -c:v h264_vaapi -an output.mp4
```

FFmpeg commands must select the acceleration method or VA-API encoder.
The FFplay desktop entry selects VA-API decoding with `-hwaccel vaapi`.
FFplay uses libplacebo for Vulkan rendering when hardware decoding is selected.
VA-API frames rendered through Venus are downloaded into CPU memory before
Vulkan uploads them. Legacy VirGL video surfaces do not provide external
memory compatible with Venus; decoding and rendering remain GPU operations.
Explicit playback commands are:

```sh
ffplay -autoexit -hwaccel vaapi input.mp4
ffplay -autoexit -enable_vulkan input.mp4
```

Vulkan video encode and decode depend on the extensions exposed by the Venus
and host Vulkan drivers. VA-API provides the configured hardware codec path.
Compiled Vulkan codecs do not establish runtime Vulkan Video support.
