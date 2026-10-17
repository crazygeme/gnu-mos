#define _GNU_SOURCE
#include <sched.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

static _Alignas(16) unsigned char stacks[8][65536];
static atomic_int start;
static int worker(void *unused)
{
    (void)unused;
    while (!atomic_load_explicit(&start, memory_order_acquire))
        syscall(SYS_sched_yield);
    syscall(SYS_exit_group, 0);
    for (;;) {}
}
int main(void)
{
    alarm(20);
    for (unsigned round = 0; round < 48; round++) {
        pid_t child = fork();
        if (child < 0) return 1;
        if (!child) {
            atomic_store(&start, 0);
            for (unsigned i = 0; i < 8; i++)
                if (clone(worker, stacks[i] + sizeof(stacks[i]),
                          CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND |
                          CLONE_THREAD | CLONE_SYSVSEM, NULL) < 0)
                    syscall(SYS_exit_group, 1);
            atomic_store_explicit(&start, 1, memory_order_release);
            syscall(SYS_exit_group, 0);
        }
        int status;
        if (waitpid(child, &status, 0) != child || !WIFEXITED(status) ||
            WEXITSTATUS(status) != 0) return 1;
    }
    puts("PASS: 48 concurrent thread-group exit rounds");
    return 0;
}
