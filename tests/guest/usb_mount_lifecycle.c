#define _GNU_SOURCE
#include <sys/mount.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define FAILED_MOUNT_ATTEMPTS 20
#define INVALID_FILESYSTEM_BYTES (8 * 1024 * 1024)
int main(int argc, char **argv)
{
    char invalid[] = "/tmp/mos-invalid-filesystem-XXXXXX";
    char directory[] = "/tmp/mos-storage-long-mountpoint-XXXXXX";
    if (argc != 2 || geteuid()) return 2;
    int fd = mkstemp(invalid);
    if (fd < 0 || ftruncate(fd, INVALID_FILESYSTEM_BYTES) || !mkdtemp(directory)) return 1;
    close(fd);
    for (unsigned i = 0; i < FAILED_MOUNT_ATTEMPTS; i++) {
        if (!mount(invalid, directory, "ext3", 0, NULL)) {
            fprintf(stderr, "Invalid filesystem was mounted\n"); return 1;
        }
    }
    unlink(invalid); rmdir(directory);
    puts("PASS repeated invalid mount cleanup");
    char path[4096], buffer[128];
    snprintf(path, sizeof(path), "%s/desktop-test.txt", argv[1]);
    fd = open(path, O_RDONLY);
    if (fd < 0 || read(fd, buffer, sizeof(buffer)) <= 0) { perror("Read mounted volume"); return 1; }
    close(fd);
    fd = open(path, O_WRONLY);
    if (fd < 0 || write(fd, "MOS", 3) != 3) { perror("Write mounted volume"); return 1; }
    close(fd); sync();
    puts("PASS mounted volume read/write after failed mount attempts");
    return 0;
}
