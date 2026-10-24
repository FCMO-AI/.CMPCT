/* O10 research client. This is NOT a general CMPCT filesystem extractor.
 * Strict root-level POSIX-only one-file-at-a-time read/write; bounded C output
 * memory, descriptor-relative O_EXCL/O_NOFOLLOW leaves. All archive parsing
 * continues to use the public native Rust C ABI.
 */
#define _POSIX_C_SOURCE 200809L
#include "native/cmpct-core/include/cmpct.h"
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>

#define CHUNK (64U * 1024U)
#define MAX_ENTRIES 4096U
#define MAX_SINGLE (128ULL * 1024ULL * 1024ULL)
#define MAX_TOTAL (512ULL * 1024ULL * 1024ULL)

static void die(const char *why, int status) {
    fprintf(stderr, "O10_FAIL %s status=%d errno=%d\n", why, status, errno);
    exit(3);
}
static void require_ok(int status, const char *why) {
    if (status != CMPCT_OK) die(why, status);
}
static void write_all(int fd, const unsigned char *buf, size_t count) {
    while (count) {
        ssize_t n = write(fd, buf, count);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) die("output write", n < 0 ? -1 : 0);
        buf += (size_t)n;
        count -= (size_t)n;
    }
}
static int safe_root_file(const char *name, size_t len) {
    if (len == 0 || len > 200 || name[0] == '.') return 0;
    if (strlen(name) != len) return 0;
    for (size_t i = 0; i < len; ++i) {
        const unsigned char c = (unsigned char)name[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '.' || c == '-' || c == '_'))
            return 0;
    }
    return 1;
}

int main(int argc, char **argv) {
    if (argc != 3) die("usage: stream ARCHIVE DEST", 0);
    CmpctArchive *archive = NULL;
    require_ok(cmpct_open(argv[1], &archive), "archive open");
    const size_t total_entries = cmpct_entry_count(archive);
    if (total_entries == 0 || total_entries > MAX_ENTRIES) die("entry budget", 0);

    int root = open(argv[2], O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (root < 0) die("destination directory", -1);
    unsigned char buffer[CHUNK];
    uint64_t total = 0;
    size_t files = 0;
    for (size_t i = 0; i < total_entries; ++i) {
        CmpctEntryInfo info;
        require_ok(cmpct_entry_info(archive, i, &info), "entry info");
        if (info.kind != 0) continue;
        if (info.size > MAX_SINGLE || total > MAX_TOTAL - info.size)
            die("aggregate logical output bound", 0);
        total += info.size;

        size_t name_len = 0;
        require_ok(cmpct_entry_path(archive, i, NULL, 0, &name_len), "path length");
        if (name_len == 0 || name_len > 200) die("unsafe path length", 0);
        char name[201];
        memset(name, 0, sizeof(name));
        require_ok(cmpct_entry_path(archive, i, name, name_len + 1, &name_len),
                   "path");
        if (!safe_root_file(name, name_len)) die("unsafe root-only path", 0);

        /* No truncate/follow: an existing leaf, including a symlink or hardlink,
         * is refused before any bytes for that member can be published.
         * This does not imply whole-tree atomicity or adversarial namespace safety.
         */
        int out = openat(root, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
        if (out < 0) die("destination leaf must not exist", -1);
        uint64_t pos = 0;
        while (pos < info.size) {
            size_t request = (size_t)(info.size - pos < CHUNK ? info.size - pos : CHUNK);
            size_t received = 0;
            require_ok(cmpct_entry_read_range(archive, i, pos, buffer, request, &received),
                       "native range");
            if (received != request) die("short native range", CMPCT_ERR_FORMAT);
            write_all(out, buffer, received);
            pos += received;
        }
        if (close(out) != 0) die("close output file", -1);
        files++;
    }
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) != 0) die("resource usage", -1);
    printf("{\"mode\":\"stream\",\"members\":%zu,\"decoded_bytes\":%" PRIu64
           ",\"max_chunk\":%u,\"rss_kib\":%ld}\n",
           files, total, (unsigned)CHUNK, ru.ru_maxrss);
    if (close(root) != 0) die("close directory", -1);
    cmpct_close(archive);
    return 0;
}
