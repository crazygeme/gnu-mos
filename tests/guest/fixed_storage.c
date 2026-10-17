/* Destructive validation for explicitly designated disposable block devices. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/fs.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

static void require(int condition, const char *operation) {
  if (!condition) {
    perror(operation);
    exit(1);
  }
}
int main(int argc, char **argv) {
  if (argc < 3 || strcmp(argv[1], "--destructive")) {
    fprintf(stderr, "Usage: %s --destructive DEVICE...\n", argv[0]);
    return 2;
  }
  for (int i = 2; i < argc; i++) {
    int fd = open(argv[i], O_RDWR);
    require(fd >= 0, "open");
    struct stat st;
    require(!fstat(fd, &st) && S_ISBLK(st.st_mode), "block device");
    uint64_t size;
    int sector;
    require(!ioctl(fd, BLKGETSIZE64, &size), "BLKGETSIZE64");
    require(!ioctl(fd, BLKSSZGET, &sector), "BLKSSZGET");
    require(size >= 8 * 1024 * 1024 && (sector == 512 || sector == 4096),
            "geometry");
    size_t length = 300 * 1024 + 37;
    uint64_t offset = 1024 * 1024 + 13;
    unsigned char *a = malloc(length), *b = malloc(length);
    require(a && b, "malloc");
    for (size_t j = 0; j < length; j++)
      a[j] = (j * 113 + (j >> 8) + i * 19) & 255;
    require(pwrite(fd, a, length, offset) == (ssize_t)length,
            "unaligned write");
    require(!ioctl(fd, BLKFLSBUF, 0), "flush");
    require(pread(fd, b, length, offset) == (ssize_t)length &&
                !memcmp(a, b, length),
            "readback");
    require(pread(fd, b, sector, size - sector) == sector, "last sector read");
    require(pread(fd, b, sector, size) == 0, "end of device");
    for (unsigned worker = 0; worker < 4; worker++) {
      pid_t pid = fork();
      require(pid >= 0, "fork");
      if (!pid) {
        uint64_t at = 8 * 1024 * 1024 + worker * 512 * 1024 + 7;
        size_t bytes = 128 * 1024 + 31;
        memset(a, 0x35 + worker, bytes);
        for (unsigned pass = 0; pass < 8; pass++) {
          require(pwrite(fd, a, bytes, at) == (ssize_t)bytes,
                  "concurrent write");
          require(
              pread(fd, b, bytes, at) == (ssize_t)bytes && !memcmp(a, b, bytes),
              "concurrent readback");
        }
        _exit(0);
      }
    }
    for (unsigned worker = 0; worker < 4; worker++) {
      int status;
      require(
          wait(&status) > 0 && WIFEXITED(status) && WEXITSTATUS(status) == 0,
          "concurrent worker");
    }
    uint64_t range[2] = {4 * 1024 * 1024, 128 * 1024};
    int discarded = ioctl(fd, BLKDISCARD, range);
    require(!discarded || (strstr(argv[i], "/hd") && errno == EOPNOTSUPP),
            "discard");
    range[0] = size;
    range[1] = sector;
    errno = 0;
    require(ioctl(fd, BLKDISCARD, range) == -1 &&
                (errno == EINVAL ||
                 (strstr(argv[i], "/hd") && errno == EOPNOTSUPP)),
            "discard bounds");
    require(!ioctl(fd, BLKFLSBUF, 0), "final flush");
    printf(
        "PASS %s bytes=%llu sector=%d unaligned=%zu flush discard bounds "
        "concurrency\n",
        argv[i], (unsigned long long)size, sector, length);
    close(fd);
    free(a);
    free(b);
  }
  return 0;
}
