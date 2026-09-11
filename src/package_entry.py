#!/usr/bin/env python3
from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("error: package build entry requires one build script", file=sys.stderr)
        return 2

    script = Path(argv[0])
    try:
        runpy.run_path(str(script), run_name="__main__")
        return 0
    except KeyboardInterrupt:
        print("error: package build interrupted", file=sys.stderr)
        return 130
    except subprocess.CalledProcessError as error:
        command = error.cmd
        if isinstance(command, (list, tuple)):
            command = " ".join(str(part) for part in command)
        print(
            f"error: command failed ({error.returncode}): {command}",
            file=sys.stderr,
        )
        return error.returncode or 1
    except OSError as error:
        print(f"error: {error.strerror or error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
