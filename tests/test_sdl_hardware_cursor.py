"""Validate SDL relative input independently of guest cursor feedback."""
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SdlHardwareCursor(unittest.TestCase):
    def test_delayed_feedback_and_button_only_events(self):
        archive = ROOT / ".workspace/sources/qemu-10.2.1.tar.xz"
        if not archive.is_file():
            self.skipTest("Configured QEMU source archive is unavailable")
        with tarfile.open(archive) as source:
            text = source.extractfile("qemu-10.2.1/ui/sdl2.c").read().decode()
            header = source.extractfile("qemu-10.2.1/include/ui/sdl2.h").read().decode()
        with tempfile.TemporaryDirectory(prefix="sdl-cursor-input-") as tmp:
            work = Path(tmp)
            (work / "ui").mkdir()
            (work / "ui/sdl2.c").write_text(text)
            (work / "include/ui").mkdir(parents=True)
            (work / "include/ui/sdl2.h").write_text(header)
            subprocess.run(["patch", "--batch", "-p1", "-i", str(
                ROOT / "src/packages/qemu-host/sdl-hardware-cursor-motion.patch")],
                cwd=work, check=True, capture_output=True)
            text = (work / "ui/sdl2.c").read_text()
            function = text[text.index("static void sdl_send_mouse_event("):
                            text.index("static void toggle_full_screen(")]
            feedback = text[text.index("static void sdl_mouse_warp("):
                            text.index("static void sdl_mouse_define(")]
            helpers = text[text.index("static void sdl_pointer_align("):
                           text.index("static void sdl_grab_start(")]
            size_case = text[text.index("    case SDL_WINDOWEVENT_SIZE_CHANGED:"):
                             text.index("    case SDL_WINDOWEVENT_RESIZED:")]
            size_event = ("static void size_event(struct sdl2_console *scon) {"
                          "switch (SDL_WINDOWEVENT_SIZE_CHANGED) {" + size_case + "}}")
            (work / "probe.c").write_text(
                HEAD + helpers + function + feedback + size_event + CASES)
            subprocess.run(["cc", "-std=gnu11", "-Wall", "-Werror",
                            str(work / "probe.c"), "-o", str(work / "probe")],
                           check=True)
            subprocess.run([str(work / "probe")], check=True, timeout=5)


HEAD = r'''
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <stddef.h>
#define INPUT_BUTTON__MAX 7
#define INPUT_BUTTON_LEFT 0
#define INPUT_BUTTON_MIDDLE 1
#define INPUT_BUTTON_RIGHT 2
#define INPUT_BUTTON_SIDE 3
#define INPUT_BUTTON_EXTRA 4
#define SDL_BUTTON_LEFT 1
#define SDL_BUTTON_MIDDLE 2
#define SDL_BUTTON_RIGHT 3
#define SDL_BUTTON_X1 4
#define SDL_BUTTON_X2 5
#define SDL_BUTTON(n) (1u << ((n)-1))
#define SDL_WINDOWEVENT_SIZE_CHANGED 1
#define INPUT_AXIS_X 0
#define INPUT_AXIS_Y 1
typedef struct DisplayChangeListener { void *con; } DisplayChangeListener;
struct sdl2_console {
    DisplayChangeListener dcl; void *surface, *real_window;
    bool pointer_valid, pointer_pending;
    int pointer_x, pointer_y;
    uint32_t pointer_input_ticks, pointer_feedback_ticks;
};
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
static bool guest_cursor;
static int gui_grab=1, absolute_enabled, guest_x, guest_y, warps, shows, hides;
static void *guest_sprite;
static uint32_t ticks;
static int window_w = 960, window_h = 540, warped_x, warped_y;
static uint32_t SDL_GetTicks(void) { return ticks; }
static void SDL_GetWindowSize(void *w, int *x, int *y) { *x=window_w; *y=window_h; }
static int qemu_console_is_graphic(void *c) { return 1; }
static void sdl_show_cursor(struct sdl2_console *s) { shows++; }
static void sdl_hide_cursor(struct sdl2_console *s) { hides++; }
static void SDL_SetCursor(void *c) {}
void SDL_WarpMouseInWindow(void *w, int x, int y) { warps++; warped_x=x; warped_y=y; }
static int absolute, relative[2], position[2], buttons, syncs;
static int surface_width(void *s) { return 1920; }
static int surface_height(void *s) { return 1080; }
static int qemu_input_is_absolute(void *c) { return absolute; }
static void qemu_input_update_buttons(void *c, uint32_t *map, int old, int now) { buttons=now; }
static void qemu_input_queue_rel(void *c, int axis, int value) { relative[axis]=value; }
static void qemu_input_queue_abs(void *c, int axis, int value, int min, int max) { position[axis]=value; }
static void qemu_input_event_sync(void) { syncs++; }
'''
CASES = r'''
int main(void) {
    struct sdl2_console s = {0};
    sdl_send_mouse_event(&s, 7, -3, 1500, 800, 0);
    assert(relative[0]==7 && relative[1]==-3);
    sdl_send_mouse_event(&s, 0, 0, 1400, 700, 1);
    assert(relative[0]==0 && relative[1]==0 && buttons==1);
    absolute=1;
    sdl_send_mouse_event(&s, 7, -3, 100, 200, 0);
    assert(position[0]==100 && position[1]==200);
    absolute=0;

    sdl_mouse_warp(&s.dcl, 600, 300, true);
    assert(warps==1 && shows==1 && guest_cursor);
    assert(warped_x==300 && warped_y==150);
    sdl_send_mouse_event(&s, 1, 0, 602, 300, 0);
    assert(relative[0]==2 && relative[1]==0 && s.pointer_pending);
    sdl_send_mouse_event(&s, 1, 0, 604, 300, 0);
    sdl_mouse_warp(&s.dcl, 602, 300, true);
    assert(s.pointer_pending && warps==1 && s.pointer_x==604);
    sdl_mouse_warp(&s.dcl, 604, 300, true);
    assert(!s.pointer_pending && warps==1);
    sdl_send_mouse_event(&s, 0, 0, 604, 300, 1);
    assert(relative[0]==0 && relative[1]==0 && buttons==1);

    /* Fractional scale steps sum exactly without integer-division loss. */
    int sum=0;
    for (int i=1; i<=100; i++) {
        int x=604+i*1920/1152;
        ticks++;
        sdl_send_mouse_event(&s, 1, 0, x, 300, 0);
        sum+=relative[0];
        sdl_mouse_warp(&s.dcl, x-1, 300, true);
        assert(s.pointer_pending && s.pointer_x==x && warps==1);
        sdl_mouse_warp(&s.dcl, x, 300, true);
    }
    assert(sum==100*1920/1152 && !s.pointer_pending);
    window_w=640; window_h=360;
    ticks+=200;
    sdl_mouse_warp(&s.dcl, 900, 600, true);
    assert(warps==2 && warped_x==300 && warped_y==200);
    assert(s.pointer_x==900 && s.pointer_y==600);
    sdl_send_mouse_event(&s, 0, 0, 900, 600, 1);
    assert(relative[0]==0 && relative[1]==0);

    /* Re-capture aligns the hotspot through the current window scale. */
    s.pointer_valid=false;
    sdl_pointer_align(&s, 1200, 750);
    assert(warped_x==400 && warped_y==250);
    sdl_send_mouse_event(&s, 1, -1, 1203, 747, 0);
    assert(relative[0]==3 && relative[1]==-3);
    sdl_mouse_warp(&s.dcl, 1203, 747, true);
    assert(!s.pointer_pending);
    window_w=1920; window_h=1080;
    guest_x=600; guest_y=400;
    size_event(&s);
    assert(warped_x==600 && warped_y==400);
    assert(s.pointer_x==600 && s.pointer_y==400 && !s.pointer_pending);
    int before=warps;
    gui_grab=0;
    window_w=1280;
    size_event(&s);
    assert(warps==before);
    gui_grab=1;
    sdl_mouse_warp(&s.dcl, 1203, 747, false);
    assert(!guest_cursor && hides==1 && !s.pointer_valid);
}
'''

if __name__ == "__main__":
    unittest.main()
