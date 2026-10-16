"""Inject the physical key sequence consumed by tests/guest/keyboard_input.py."""

import argparse
import json
import socket
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("socket", help="Local QEMU QMP Unix socket")
    parser.add_argument("--cycles", type=int, default=100)
    parser.add_argument("--interval", type=float, default=.005,
                        help="Delay between physical key transitions in seconds")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval <= 0:
        parser.error("Cycle count and transition interval must be positive")
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(10)
        connection.connect(args.socket)
        with connection.makefile("rwb", buffering=0) as stream:
            assert "QMP" in json.loads(stream.readline())

            def call(command, arguments=None):
                stream.write((json.dumps(dict(execute=command, arguments=arguments or {})) + "\n").encode())
                while True:
                    line = stream.readline()
                    if not line:
                        raise EOFError("QMP connection closed")
                    response = json.loads(line)
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    if "return" in response:
                        return response["return"]

            call("qmp_capabilities")

            def key(name, down):
                call("input-send-event", {"events": [dict(
                    type="key", data=dict(down=down, key=dict(type="qcode", data=name)))]})
                time.sleep(args.interval)

            def tap(name):
                key(name, True)
                key(name, False)

            for cycle in range(args.cycles):
                tap("dot")
                key("shift", True)
                tap("dot")
                key("shift", False)
                tap("dot")
                tap("a")
                key("shift_r", True)
                tap("a")
                key("shift_r", False)
                tap("a")
                tap("caps_lock")
                tap("a")
                tap("dot")
                key("shift", True)
                tap("a")
                key("shift", False)
                tap("caps_lock")
                tap("dot")
                call("input-send-event", {"events": [dict(
                    type="rel", data=dict(axis="x", value=1 if cycle % 2 else -1))]})
    print(f"Injected {args.cycles} keyboard cycles with mouse motion")


if __name__ == "__main__":
    main()
