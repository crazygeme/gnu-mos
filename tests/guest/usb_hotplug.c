/* Validate removal, stale descriptors, sysfs lifetime, and repeated insertion. */
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define SECTOR_SIZE 512
#define WAIT_SECONDS 15
static int wait_device(int present)
{
    for (unsigned attempt = 0; attempt < WAIT_SECONDS * 100; attempt++) {
        if ((access("/dev/sda", F_OK) == 0) == present) return 0;
        usleep(10000);
    }
    return -1;
}
static int stale_read(int fd)
{
    char sector[SECTOR_SIZE];
    lseek(fd, 0, SEEK_SET);
    errno = 0;
    return read(fd, sector, sizeof(sector)) == -1 && errno == ENODEV;
}
int main(int argc, char **argv)
{
    unsigned cycles = argc > 1 ? (unsigned)atoi(argv[1]) : 6;
    setvbuf(stdout, NULL, _IONBF, 0);
    for (unsigned cycle = 0; cycle < cycles; cycle++) {
        unsigned char expected[SECTOR_SIZE], actual[SECTOR_SIZE];
        int old = open("/dev/sda", O_RDONLY);
        if (old < 0 || read(old, expected, sizeof(expected)) != sizeof(expected)) {
            perror("initial USB read"); return 1;
        }
        DIR *drivers = opendir("/sys/bus/usb/drivers/usb-storage");
        struct dirent *entry;
        char sysfs[256] = {0}, alias_path[256] = {0};
        if (!drivers) { perror("USB driver inventory"); return 1; }
        while ((entry = readdir(drivers))) {
            if (entry->d_name[0] == '.') continue;
            snprintf(sysfs, sizeof(sysfs), "/sys/bus/usb/devices/%s/idVendor", entry->d_name);
            snprintf(alias_path, sizeof(alias_path), "/sys/bus/usb/drivers/usb-storage/%s", entry->d_name);
            break;
        }
        closedir(drivers);
        int attribute = open(sysfs, O_RDONLY);
        int alias = open(alias_path, O_PATH | O_NOFOLLOW);
        if (attribute < 0 || alias < 0) { perror("USB sysfs references"); return 1; }
        printf("USB_REMOVE_READY %u\n", cycle);
        if (wait_device(0) || !stale_read(old) || access(sysfs, F_OK) == 0) {
            fprintf(stderr, "Removal failed at cycle %u errno=%d\n", cycle, errno); return 1;
        }
        char vendor[16];
        if (read(attribute, vendor, sizeof(vendor)) <= 0) {
            perror("retained sysfs attribute"); return 1;
        }
        printf("USB_ADD_READY %u\n", cycle);
        if (wait_device(1) || !stale_read(old)) {
            fprintf(stderr, "Stale descriptor reused at cycle %u\n", cycle); return 1;
        }
        int fresh = open("/dev/sda", O_RDONLY);
        if (fresh < 0 || read(fresh, actual, sizeof(actual)) != sizeof(actual) ||
            memcmp(expected, actual, sizeof(actual))) {
            perror("reinserted USB read"); return 1;
        }
        close(fresh); close(old); close(attribute); close(alias);
        printf("USB_HOTPLUG_OK %u\n", cycle);
    }
    puts("USB_HOTPLUG_ALL_OK");
    return 0;
}
