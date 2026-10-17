# ALSA audio playback

MOS exposes the USB Audio Class 1 playback device through the native ALSA
PCM and control interfaces. The device nodes are `/dev/snd/controlC0` and
`/dev/snd/pcmC0D0p`, with Linux major number 116. The card identifier is
`MOSUSB`; the PCM device is `hw:0,0`.

The hardware stream uses 48000 Hz, two interleaved channels and signed
16-bit little-endian samples. Both `RW_INTERLEAVED` and `MMAP_INTERLEAVED`
access are supported. `/etc/asound.conf` selects the ALSA `plug` interface
for `default`, permitting userspace sample format, channel and rate
conversion. The default control interface selects card zero. The configured host QEMU
resolves scheduled USB Frame IDs in the nearest 2048 ms epoch.

PCM configuration includes hardware constraint refinement, software
thresholds, shared status and control mappings, frame transfer, readiness
notifications, delay reporting, prepare, start, drop, drain and underrun
recovery. Hardware position advances on each completed USB packet. ALSA transport
submission is nonblocking, allowing position and readiness queries while
both USB transfer banks are active. Shared PCI xHCI interrupts dispatch event
processing through the deferred callback worker. Packet completion wakes the
ALSA worker directly; periodic polling provides a fallback. Full-speed USB
playback uses an explicit frame timeline across queued transfers. PCM ring
wrap boundaries preserve complete USB audio packets. Each USB transfer
contains at most 1536 frames. The PCM ring is bounded to 256 KiB.

The control interface exposes stereo `PCM Playback Volume` values from zero
to 100 and stereo `PCM Playback Switch` values. Subscribed control handles
receive value-change events. `/proc/asound` exposes card, device, PCM and
active stream configuration and position information.

The card provides one playback substream. Concurrent hardware playback
opens are unavailable. Capture, hardware pause, MIDI and sequencer devices
are not provided by this card. The native x64 ALSA interface is used by
Microsoft Edge. OSS device nodes remain available for OSS applications.

## Headless playback

The project launcher attaches the USB audio device to the xHCI controller.
Host output defaults to 48000 Hz. An explicit `out.frequency` value in
`MOS_AUDIO_BACKEND` overrides this default. SDL is the default audio backend.
A PulseAudio-compatible host server can be selected without changing QEMU:

```sh
MOS_AUDIO_BACKEND=pa,out.frequency=48000 MOS_USB_CAMERA=none ./lfs run -- \
  -display egl-headless \
  -vnc 127.0.0.1:9
```

The PulseAudio-compatible host endpoint may be provided by PipeWire. Host
speaker routing and microphone selection are controlled by the active host
audio session. An audio backend of `none` does not produce audible output.

## Guest verification

The guest programs require the installed ALSA headers, library and math
library:

```sh
gcc tests/guest/alsa_control.c -o /tmp/alsa-control -lasound -lm
gcc tests/guest/alsa_pcm.c -o /tmp/alsa-pcm -lasound -lm
/tmp/alsa-control
/tmp/alsa-pcm hw:0,0 48000 10 0 85500
/tmp/alsa-pcm hw:0,0 48000 10 1 85500
/tmp/alsa-pcm default 44100 10 0
```

The PCM arguments select device, sample rate, duration, mmap mode and
latency in microseconds. A latency of 85500 microseconds configures a
4104-frame hardware buffer and 1026-frame period at 48000 Hz.
The test reports transferred frames, underruns and elapsed time. The
control test validates enumeration, value changes, notifications and
hardware parameter rejection.

`tests/audio_capture.py` records the host microphone and output monitor
while executing a playback command. The playback command must establish
its own guest connection. Credentials must not be included in command
arguments or output files.

```sh
python3 tests/audio_capture.py --output-dir .workspace/x64/logs \
  --name tone --frequency 660 -- guest-playback-command
```

Recordings use 48000 Hz stereo S16_LE PCM. Analysis reports signal level,
near-reference dominant frequency, sample discontinuity magnitude and
10 ms intervals below one quarter of the steady signal level. Reference-tone
checks also reject digital monitor silence runs of at least 1 ms and sample
steps above twice the expected sinusoidal maximum. The microphone derivative
is reported separately because room noise and microphone response alter it. A recording
without a detectable signal does not establish successful playback.
Microphone recordings include the host speaker response, room acoustics
and background noise. Output monitor recordings describe the digital
host output signal.

For browser verification, `/usr/bin/microsoft-edge` opens
`https://haokan.baidu.com/`. A selected video must advance with audio
unmuted and without an audio renderer error. Browser automation requiring
a DevTools port uses a separate data directory and a loopback listener.

`tests/guest/browser_audio.py` validates an existing video page through a
loopback DevTools endpoint. It checks HTTPS page state, JavaScript, Canvas,
unmuted audio, decoder progress and media progress in five-second intervals.
An interval below 85 percent of elapsed time fails the continuity check.
The endpoint may be forwarded over SSH to the host for microphone capture.

```sh
python3 tests/guest/browser_audio.py --port 19222 --seconds 60
```

A browser-generated reference tone exercises Web Audio and the ALSA output
path through the same browser audio service:

```sh
python3 tests/audio_capture.py --output-dir .workspace/x64/logs \
  --name browser-tone --frequency 660 -- \
  python3 tests/guest/browser_tone.py --port 19222 --seconds 15
```
