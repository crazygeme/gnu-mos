"""Validate physical keyboard events delivered to an X11 desktop window."""

import argparse
import ctypes as C
import json
import time


class KeyEvent(C.Structure):
    _fields_ = [
        ("type", C.c_int), ("serial", C.c_ulong), ("send_event", C.c_int),
        ("display", C.c_void_p), ("window", C.c_ulong), ("root", C.c_ulong),
        ("subwindow", C.c_ulong), ("time", C.c_ulong), ("x", C.c_int),
        ("y", C.c_int), ("x_root", C.c_int), ("y_root", C.c_int),
        ("state", C.c_uint), ("keycode", C.c_uint), ("same_screen", C.c_int),
    ]


class Event(C.Union):
    _fields_ = [("type", C.c_int), ("key", KeyEvent), ("pad", C.c_long * 24)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--output", default="/tmp/keyboard-input.jsonl")
    args = parser.parse_args()
    if args.cycles < 1 or args.timeout <= 0:
        parser.error("Cycle count and timeout must be positive")
    x = C.CDLL("libX11.so.6")
    signatures = {
        "XOpenDisplay": ([C.c_char_p], C.c_void_p),
        "XDefaultRootWindow": ([C.c_void_p], C.c_ulong),
        "XCreateSimpleWindow": ([C.c_void_p, C.c_ulong, C.c_int, C.c_int,
                                 C.c_uint, C.c_uint, C.c_uint, C.c_ulong, C.c_ulong], C.c_ulong),
        "XSelectInput": ([C.c_void_p, C.c_ulong, C.c_long], C.c_int),
        "XStoreName": ([C.c_void_p, C.c_ulong, C.c_char_p], C.c_int),
        "XMapWindow": ([C.c_void_p, C.c_ulong], C.c_int),
        "XSync": ([C.c_void_p, C.c_int], C.c_int),
        "XGrabKeyboard": ([C.c_void_p, C.c_ulong, C.c_int, C.c_int, C.c_int, C.c_ulong], C.c_int),
        "XPending": ([C.c_void_p], C.c_int),
        "XNextEvent": ([C.c_void_p, C.POINTER(Event)], C.c_int),
        "XLookupString": ([C.POINTER(KeyEvent), C.c_char_p, C.c_int,
                           C.POINTER(C.c_ulong), C.c_void_p], C.c_int),
        "XQueryKeymap": ([C.c_void_p, C.c_char_p], C.c_int),
        "XCloseDisplay": ([C.c_void_p], C.c_int),
    }
    for name, (arguments, result) in signatures.items():
        getattr(x, name).argtypes = arguments
        getattr(x, name).restype = result
    display = x.XOpenDisplay(None)
    assert display, "The desktop X11 display could not be opened"
    try:
        window = x.XCreateSimpleWindow(display, x.XDefaultRootWindow(display),
                                       30, 30, 640, 120, 0, 0, 0xffffff)
        x.XSelectInput(display, window, 3)
        x.XStoreName(display, window, b"MOS keyboard input validation")
        x.XMapWindow(display, window)
        x.XSync(display, 0)
        # The window manager must process the mapping before the grab.
        time.sleep(1)
        assert x.XGrabKeyboard(display, window, 0, 1, 1, 0) == 0, "Keyboard grab failed"
        x.XSync(display, 0)
        print("READY", flush=True)
        expected = ".>.aAaA.a." * args.cycles
        text = ""
        events = 0
        deadline = time.monotonic() + args.timeout
        complete_at = None
        with open(args.output, "w") as log:
            while time.monotonic() < deadline:
                if not x.XPending(display):
                    if complete_at is not None and time.monotonic() - complete_at > 1:
                        break
                    time.sleep(.002)
                    continue
                event = Event()
                x.XNextEvent(display, C.byref(event))
                if event.type not in (2, 3):
                    continue
                buffer = C.create_string_buffer(32)
                symbol = C.c_ulong()
                size = x.XLookupString(C.byref(event.key), buffer, 32, C.byref(symbol), None)
                value = buffer.raw[:size].decode("latin1")
                log.write(json.dumps(dict(type=event.type, code=event.key.keycode,
                                          state=event.key.state, symbol=hex(symbol.value), text=value)) + "\n")
                log.flush()
                events += 1
                if event.type == 2:
                    text += value
                if len(text) >= len(expected) and complete_at is None:
                    complete_at = time.monotonic()
        keys = C.create_string_buffer(32)
        x.XQueryKeymap(display, keys)
        pressed = [i for i in range(256) if keys.raw[i // 8] & (1 << (i % 8))]
        print(json.dumps(dict(events=events, characters=len(text), expected=len(expected),
                              keys_down=pressed, text_matches=text == expected)), flush=True)
        assert text == expected, "Keyboard text differs from the injected sequence"
        assert events == args.cycles * 30, "Keyboard press/release event count differs"
        assert not pressed, "A key remains pressed after the sequence"
        print("Keyboard Shift, Caps Lock, punctuation, and release checks passed", flush=True)
    finally:
        x.XCloseDisplay(display)


if __name__ == "__main__":
    main()
