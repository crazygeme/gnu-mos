/* USB input validation with QEMU monitor key and relative-pointer injection. */
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <time.h>
#include <errno.h>
#include <string.h>
#include <linux/kd.h>
#include <linux/vt.h>

int main(int argc, char **argv)
{
    int release_only = argc > 1 && strcmp(argv[1], "--release") == 0;
    int keyboard = open("/dev/tty9", O_RDWR | O_NONBLOCK);
    int mouse = open("/dev/input/mice", O_RDWR | O_NONBLOCK);
    struct termios saved, raw;
    int mode = 0;
    const int console = 9;
    if (keyboard < 0 || mouse < 0 || tcgetattr(keyboard, &saved) ||
        ioctl(keyboard, KDGKBMODE, &mode)) {
        perror("input initialization"); return 1;
    }
    raw = saved; cfmakeraw(&raw);
    if (tcsetattr(keyboard, TCSANOW, &raw) || ioctl(keyboard, KDSKBMODE, K_MEDIUMRAW) ||
        ioctl(keyboard, VT_ACTIVATE, console)) {
        perror("console configuration"); return 1;
    }
    unsigned char buf[128];
    while (read(keyboard, buf, sizeof(buf)) > 0) {}
    while (read(mouse, buf, sizeof(buf)) > 0) {}
    if (ioctl(keyboard, KDSETLED, LED_NUM) || ioctl(keyboard, KDSETLED, 0)) {
        perror("USB keyboard LEDs"); return 1;
    }
    puts("USB_LED_OK");
    puts("USB_INPUT_READY"); fflush(stdout);
    int a = 0, a_up = 0, shift = 0, shift_release = 0, up = 0, movement = 0, button = 0, button_release = 0;
    unsigned char packet[4]; unsigned packet_bytes = 0;
    const unsigned char imps2[] = {0xf3, 200, 0xf3, 100, 0xf3, 80};
    write(mouse, imps2, sizeof(imps2));
    while (read(mouse, buf, sizeof(buf)) > 0) {}
    struct timespec start, now;
    clock_gettime(CLOCK_MONOTONIC, &start);
    do {
        int n = read(keyboard, buf, sizeof(buf));
        for (int i = 0; i < n; i++) {
            printf("key=%02x\n", buf[i]);
            if (buf[i] == 30) a++;
            if (buf[i] == (30 | 128)) a_up++;
            if (buf[i] == 42) shift++;
            if (buf[i] == (42 | 128)) shift_release++;
            if (buf[i] == 103) up++;
        }
        n = read(mouse, buf, sizeof(buf));
        if (n > 0) {
            printf("mouse:"); for (int i = 0; i < n; i++) printf(" %02x", buf[i]); puts("");
            for (int i = 0; i < n; i++) {
                packet[packet_bytes++] = buf[i];
                if (packet_bytes == sizeof(packet)) {
                    if (packet[1] || packet[2]) movement++;
                    if (packet[0] & 1) button++;
                    else if (button) button_release++;
                    packet_bytes = 0;
                }
            }
        }
        usleep(10000);
        clock_gettime(CLOCK_MONOTONIC, &now);
    } while (now.tv_sec - start.tv_sec < 7);
    ioctl(keyboard, KDSKBMODE, mode); tcsetattr(keyboard, TCSANOW, &saved);
    ioctl(keyboard, VT_ACTIVATE, 1);
    close(keyboard); close(mouse);
    printf("a=%d release=%d shift=%d up=%d movement=%d button=%d\n", a, a_up, shift, up, movement, button);
    if (release_only) {
        printf("USB_RELEASE %d %d %d %d\n", shift, shift_release, button, button_release);
        return !(shift && shift_release && button && button_release);
    }
    return !(a >= 2 && a_up >= 2 && shift && up && movement && button);
}
