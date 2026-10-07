# Mesa Build and Diagnostics

Mesa 25.1.9 is cross-compiled with the VirGL Gallium driver, OpenGL, EGL,
and VA-API support. All video codecs are enabled. The VA-API frontend depends
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
