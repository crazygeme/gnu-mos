#!/usr/bin/env python3
"""Validate downstream USB removal and hub subtree lifetimes through QMP.

Requires two hubs at ports 6 and 6.1, with usb-disk at 6.1.3. The guest
usb_hotplug executable must be installed at the configured path. The SSH
command must provide a privileged guest shell without an interactive prompt.
"""
import argparse
import json
import os
import select
import shlex
import socket
import subprocess
import time


class QMP:
    def __init__(self, path):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.settimeout(15)
        self.socket.connect(path)
        self.events = []
        self.stream = self.socket.makefile("rwb", buffering=0)
        json.loads(self.stream.readline())
        self.execute("qmp_capabilities")

    def remove(self, name):
        self.execute("device_del", id=name)
        while True:
            for event in self.events:
                if event.get("event") == "DEVICE_DELETED" and event.get("data", {}).get("device") == name:
                    self.events.remove(event)
                    return
            self.events.append(json.loads(self.stream.readline()))

    def add_storage(self):
        deadline = time.monotonic() + 5
        while True:
            try:
                self.execute("device_add", driver="usb-storage", id="usb-disk",
                             bus="usb.0", port="6.1.3", drive="usbdata", removable=True)
                return
            except RuntimeError as error:
                if "Permission conflict on node" not in str(error) or time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)

    def execute(self, command, **arguments):
        request = {"execute": command}
        if arguments:
            request["arguments"] = arguments
        self.stream.write(json.dumps(request).encode() + b"\n")
        while True:
            response = json.loads(self.stream.readline())
            if "event" in response:
                self.events.append(response)
            if "error" in response:
                raise RuntimeError(response["error"])
            if "return" in response:
                return response["return"]


def run_case(qmp, ssh, guest_test, cycles, hub):
    guest_command = (
        "for attempt in $(seq 1 150); do test -b /dev/sda && break; sleep 0.1; done; exec "
        + shlex.join([guest_test, str(cycles)])
    )
    command = [*ssh, guest_command]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    pending = b""
    deadline = time.monotonic() + cycles * 40 + 20
    passed = False
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([process.stdout], [], [], 1)
            if not ready:
                continue
            data = os.read(process.stdout.fileno(), 4096)
            if not data:
                break
            pending += data
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                line = line.decode(errors="replace")
                print(line, flush=True)
                if line.startswith("USB_REMOVE_READY"):
                    if hub:
                        qmp.remove(hub)
                    else:
                        qmp.remove("usb-disk")
                elif line.startswith("USB_ADD_READY"):
                    if hub:
                        if hub == "hub1":
                            qmp.execute("device_add", driver="usb-hub", id="hub1",
                                        bus="usb.0", port="6")
                        qmp.execute("device_add", driver="usb-hub", id="hub2",
                                    bus="usb.0", port="6.1")
                        for driver, name, port in [
                            ("usb-kbd", "usb-keyboard", "6.1.1"),
                            ("usb-mouse", "usb-mouse", "6.1.2"),
                        ]:
                            qmp.execute("device_add", driver=driver, id=name,
                                        bus="usb.0", port=port)
                        qmp.add_storage()
                    else:
                        qmp.add_storage()
                elif line == "USB_HOTPLUG_ALL_OK":
                    passed = True
        status = process.wait(timeout=5)
        if not passed or status:
            raise RuntimeError(f"USB lifecycle validation failed: hub={hub}, status={status}")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        process.stdout.close()
    print(f"PASS {hub or 'downstream-device'} cycles={cycles}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qmp", required=True)
    parser.add_argument("--ssh-command", required=True,
                        help="SSH command prefix providing a privileged guest shell")
    parser.add_argument("--guest-test", default="/tmp/usb-hub-tests/usb_hotplug")
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--hubs", nargs="*", default=["hub2", "hub1"])
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error("--cycles must be positive")
    qmp = QMP(args.qmp)
    try:
        for hub in [None, *args.hubs]:
            run_case(qmp, shlex.split(args.ssh_command), args.guest_test, args.cycles, hub)
    finally:
        qmp.stream.close()
        qmp.socket.close()


if __name__ == "__main__":
    main()
