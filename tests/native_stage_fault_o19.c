/* O19 deterministic Linux fault injection. NOT a CMPCT product component.
 * A successful write()/linkat() can be surrounded by a one-byte stage
 * mutation without altering native Reader or archive bytes. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

#define STAGE ".cmpct-o18-stage"
static int injected;
static int stage_path(int fd, char path[4096]) {
    char proc[64];
    int n = snprintf(proc, sizeof(proc), "/proc/self/fd/%d", fd);
    if (n <= 0 || (size_t)n >= sizeof(proc)) return 0;
    ssize_t len = readlink(proc, path, 4095);
    if (len <= 0) return 0;
    path[len] = '\0';
    const char *base = strrchr(path, '/');
    return base && strcmp(base + 1, STAGE) == 0;
}
static int flip_byte(int fd) {
    unsigned char old;
    if (pread(fd, &old, 1, 0) != 1) return -1;
    unsigned char changed = (unsigned char)(old ^ 1U);
    if (pwrite(fd, &changed, 1, 0) != 1 || fsync(fd)) return -1;
    injected = 1;
    static const char marker[] = "O19_INJECTED_STAGE_BYTE\\n";
    (void)syscall(SYS_write, STDERR_FILENO, marker, sizeof(marker)-1);
    return 0;
}
ssize_t write(int fd, const void *buf, size_t count) {
    static ssize_t (*underlying)(int,const void*,size_t);
    if (!underlying) underlying = dlsym(RTLD_NEXT, "write");
    if (!underlying) { errno=ENOSYS; return -1; }
    ssize_t done = underlying(fd,buf,count);
    const char *point = getenv("O19_FAULT_POINT");
    char path[4096];
    if (done > 0 && !injected && point && strcmp(point,"write")==0 &&
        stage_path(fd,path)) {
        int x = open(path,O_RDWR|O_NOFOLLOW|O_CLOEXEC);
        if (x >= 0) { (void)flip_byte(x); close(x); }
    }
    return done;
}
int linkat(int oldfd,const char *oldpath,int newfd,const char *newpath,int flags) {
    static int (*underlying)(int,const char*,int,const char*,int);
    if (!underlying) underlying = dlsym(RTLD_NEXT,"linkat");
    if (!underlying) { errno=ENOSYS; return -1; }
    const char *point=getenv("O19_FAULT_POINT");
    if (!injected && point && strcmp(point,"linkat")==0 &&
        strcmp(oldpath,STAGE)==0) {
        int x=openat(oldfd,oldpath,O_RDWR|O_NOFOLLOW|O_CLOEXEC);
        if (x>=0) { (void)flip_byte(x); close(x); }
    }
    return underlying(oldfd,oldpath,newfd,newpath,flags);
}
