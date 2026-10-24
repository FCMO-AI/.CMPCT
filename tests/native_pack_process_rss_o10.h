/* O10b measurement-only Linux shim, force-included into both C evidence clients.
 * getrusage(RUSAGE_SELF).ru_maxrss on Linux can inherit a high-water mark
 * from the Python parent across fork/exec. It is NOT a sound per-executable
 * memory comparator in our subprocess harness. Instead read this process's
 * post-exec mm-specific /proc/self/status VmHWM and replace only ru_maxrss
 * before the unchanged O7/O10 printf. No product or reader ABI behavior changes.
 *
 * Macro definition follows the actual libc getrusage call to avoid recursion.
 */
#ifndef CMPCT_NATIVE_O10_RSS_SHIM_H
#define CMPCT_NATIVE_O10_RSS_SHIM_H
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/resource.h>

static int o10_process_local_rusage(int who, struct rusage *usage) {
    if (who != RUSAGE_SELF) {
        errno = EINVAL;
        return -1;
    }
    if (getrusage(who, usage) != 0) return -1;
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return -1;
    char line[512];
    long peak_kib = -1;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "VmHWM:", 6) == 0) {
            if (sscanf(line, "VmHWM: %ld kB", &peak_kib) != 1 ||
                peak_kib < 0) {
                peak_kib = -1;
            }
            break;
        }
    }
    int closed = fclose(f);
    if (peak_kib < 0 || closed != 0) {
        errno = EIO;
        return -1;
    }
    usage->ru_maxrss = peak_kib;
    return 0;
}
#define getrusage(who, usage) o10_process_local_rusage((who), (usage))
#endif
