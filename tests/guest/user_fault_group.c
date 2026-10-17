#define _GNU_SOURCE
#include <assert.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <ucontext.h>
#include <unistd.h>

static int mode, output;
static void handler(int sig, siginfo_t *info, void *context)
{
	ucontext_t *uc = context;
	int result[] = {sig, info->si_code,
		       (int)uc->uc_mcontext.gregs[REG_TRAPNO]};
	if (write(output, result, sizeof(result)) != sizeof(result))
		syscall(SYS_exit_group, 2);
	syscall(SYS_exit_group, 0);
	__builtin_unreachable();
}

static int fault_worker(void *unused)
{
	(void)unused;
	if (mode == 0)
		__asm__ volatile("ud2");
	else if (mode == 1)
		__asm__ volatile("int3");
	else
		__asm__ volatile("hlt");
	return 3;
}

int main(void)
{
	const int signals[] = {SIGILL, SIGTRAP, SIGSEGV};
	const int codes[] = {2, 128, 128};
	const int traps[] = {6, 3, 13};
	alarm(30);
	for (int caught = 0; caught < 2; caught++) {
		for (mode = 0; mode < 3; mode++) {
			int fds[2], status;
			assert(pipe(fds) == 0);
			pid_t pid = fork();
			assert(pid >= 0);
			if (!pid) {
				close(fds[0]);
				output = fds[1];
				struct sigaction action = {0};
				action.sa_flags = SA_SIGINFO;
				action.sa_sigaction = handler;
				assert(sigaction(signals[mode], caught ? &action :
						 &(struct sigaction){.sa_handler = SIG_DFL}, NULL) == 0);
				void *stack = mmap(NULL, 65536, PROT_READ | PROT_WRITE,
						   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
				assert(stack != MAP_FAILED);
				int flags = CLONE_VM | CLONE_FS | CLONE_FILES |
					    CLONE_SIGHAND | CLONE_THREAD | CLONE_SYSVSEM;
				assert(clone(fault_worker, (char *)stack + 65536,
					     flags, NULL) >= 0);
				for (;;)
					pause();
			}
			close(fds[1]);
			if (caught) {
				int result[3];
				assert(read(fds[0], result, sizeof(result)) == sizeof(result));
				assert(result[0] == signals[mode] && result[1] == codes[mode] &&
				       result[2] == traps[mode]);
			}
			close(fds[0]);
			assert(waitpid(pid, &status, 0) == pid);
			if (caught)
				assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
			else
				assert(WIFSIGNALED(status) && WTERMSIG(status) == signals[mode]);
		}
	}
	puts("User fault signals and thread-group termination validation passed");
	return 0;
}
