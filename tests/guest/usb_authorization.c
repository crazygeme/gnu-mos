/* Invoke the storage service under the non-administrative messagebus account. */
#include <grp.h>
#include <unistd.h>
#include <stdio.h>
#define TEST_ACCOUNT_ID 81
int main(int argc, char **argv)
{
    if (argc != 2 || geteuid()) return 2;
    if (setgroups(0, NULL) || setgid(TEST_ACCOUNT_ID) || setuid(TEST_ACCOUNT_ID)) {
        perror("Set test account"); return 2;
    }
    execl("/usr/bin/gdbus", "gdbus", "call", "--system", "--dest", "org.mos.Storage1",
          "--object-path", "/org/mos/Storage1", "--method", "org.mos.Storage1.Mount", argv[1], NULL);
    perror("Execute storage authorization check");
    return 2;
}
