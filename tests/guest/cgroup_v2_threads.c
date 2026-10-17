#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/futex.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "%d: %s: %s\n", __LINE__, #x, strerror(errno)); \
    exit(1); } } while (0)
static int ready[2], finish[2];
static int child_tid;

static int worker(void *unused)
{
    (void)unused;
    int tid = syscall(SYS_gettid);
    char byte;
    if (write(ready[1], &tid, sizeof(tid)) != sizeof(tid) ||
        read(finish[0], &byte, 1) != 1)
        syscall(SYS_exit, 1);
    syscall(SYS_exit, 0);
    return 0;
}

static void write_value(const char *group, const char *name, const char *value)
{
    char path[4096];
    CHECK(snprintf(path, sizeof(path), "%s/%s", group, name) < sizeof(path));
    int fd = open(path, O_WRONLY);
    CHECK(fd >= 0);
    CHECK(write(fd, value, strlen(value)) == (ssize_t)strlen(value));
    CHECK(close(fd) == 0);
}

static int read_ids(const char *group, const char *name, int first, int second)
{
    char path[4096], buffer[4096];
    CHECK(snprintf(path, sizeof(path), "%s/%s", group, name) < sizeof(path));
    int fd = open(path, O_RDONLY);
    CHECK(fd >= 0);
    int n = read(fd, buffer, sizeof(buffer)-1);
    CHECK(n >= 0);
    buffer[n] = 0;
    close(fd);
    int found = 0, total = 0;
    char *p = buffer;
    while (*p) {
        char *end;
        int id = strtol(p, &end, 10);
        CHECK(end != p);
        if (id == first) found |= 1;
        if (id == second) found |= 2;
        total++;
        p = end;
        while (*p == '\n') p++;
    }
    CHECK(found == (second ? 3 : 1));
    return total;
}

int main(int argc, char **argv)
{
    CHECK(argc == 2);
    CHECK(pipe(ready) == 0 && pipe(finish) == 0);
    char *stack = malloc(65536);
    CHECK(stack);
    int flags = CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND |
                CLONE_THREAD | CLONE_CHILD_SETTID | CLONE_CHILD_CLEARTID;
    CHECK(clone(worker, stack + 65536, flags, NULL, NULL, NULL, &child_tid) > 0);
    int tid;
    CHECK(read(ready[0], &tid, sizeof(tid)) == sizeof(tid));
    char number[32];
    snprintf(number, sizeof(number), "%d", tid);
    write_value(argv[1], "cgroup.procs", number);
    CHECK(read_ids(argv[1], "cgroup.procs", getpid(), 0) == 1);
    CHECK(read_ids(argv[1], "cgroup.threads", getpid(), tid) == 2);
    write_value(argv[1], "pids.max", "2");
    errno = 0;
    CHECK(fork() == -1 && errno == EAGAIN);
    CHECK(write(finish[1], "x", 1) == 1);
    while (__atomic_load_n(&child_tid, __ATOMIC_ACQUIRE)) {
        int value = __atomic_load_n(&child_tid, __ATOMIC_RELAXED);
        if (value) syscall(SYS_futex, &child_tid, FUTEX_WAIT, value, NULL, NULL, 0);
    }
    CHECK(read_ids(argv[1], "cgroup.threads", getpid(), 0) == 1);
    free(stack);
    puts("PASS: cgroup v2 process migration by TID and thread accounting");
    return 0;
}
