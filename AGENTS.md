# Project Documentation Rules

- Changes requiring recompilation must increment the integer in the affected package's `src/packages/<package>/version` file. Agents must not increment or synchronize the `version` field in existing `*.done` completion markers; the build process records the configured build version only after successful compilation. The automatic initialization of markers without a `version` field remains part of the status and build scanning logic.
- Documentation must describe only the current implementation, configuration, behavior, and supported usage.
- Do not mention historical states, previous implementations, migrations, former defects, or earlier decisions unless they are required to define current behavior.
- Do not mention that information came from the user, from a request, or from a conversation.
- Do not include process narration, drafting notes, conversational context, or speculative future status in project documentation.
- Use formal, precise, impersonal language throughout documentation, comments, command help, and generated status text.
- When a limitation is relevant, describe it as a current technical constraint and state its observable impact.
- Version, package, and compatibility information must identify the currently configured values only.
- Build errors must be fixed through package configuration, build flags, dependency declarations, or external patches; do not modify upstream source files directly.
- MOS is an exception to the upstream source modification restriction: modify its source directly in `.workspace/sources/mos`. Do not use or modify `../mos`. MOS source changes requiring recompilation must increment `src/packages/mos/version`.
- When a failure is caused by a missing library or development dependency, add and build the required package, headers, library paths, and build-order dependency. Do not disable the affected component to avoid the dependency.
- If build parameters cannot resolve a source compatibility error, add a separate patch file in the package directory beside `build.py` and apply it before compilation. Upstream archives and checkouts must remain unmodified.
- Every package patch must be validated with `patch --dry-run` against a fresh extraction of the exact configured source archive before it is used by `build.py`.
- After modifying files, do not start or run compilation automatically. Compilation may be run only when explicitly requested.
- Prefer verified domestic mirrors for package downloads. Retain the upstream URL when a domestic mirror is unavailable or cannot be verified.
- `./lfs setup` runs package postscript files and copies the configured sysroot into the bootable image. Keep system configuration in package postscript files or `src/sysroot`; do not add package-completeness, executable-format, or individual-file checks to `setup`.
