/* O11 research-only: operation-scoped Zstd-owner batching with bounded output staging.
 * Compose O7 physical coalescing and O10 64-KiB RAW streaming, while preserving
 * both unmodified source-exact controls. Not a general filesystem extractor:
 * POSIX-only, root-level fixture names, file-by-file publication, mutable-source
 * and crash recovery not established. Parser and authentication are in Rust ABI.
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

#define MAX_ENTRIES 4096U
#define MAX_NAME 200U
#define MAX_SINGLE (128ULL * 1024ULL * 1024ULL)
#define MAX_TOTAL (512ULL * 1024ULL * 1024ULL)
#define MAX_BATCH (16U * 1024U * 1024U)
#define MAX_RANGES 1024U
#define CHUNK (64U * 1024U)

typedef struct Item {
    size_t index, owner;
    uint64_t size;
    char name[MAX_NAME + 1];
    int eligible, done;
} Item;

static void die(const char *why, int status) {
    fprintf(stderr, "O11_FAIL %s status=%d errno=%d\n", why, status, errno);
    exit(3);
}
static void ok(int rc, const char *why) {
    if (rc != CMPCT_OK) die(why, rc);
}
static void write_all(int fd, const uint8_t *buf, size_t n) {
    while (n > 0) {
        ssize_t w = write(fd, buf, n);
        if (w < 0 && errno == EINTR) continue;
        if (w <= 0) die("write", -1);
        buf += (size_t)w;
        n -= (size_t)w;
    }
}
static int safe_name(const char *s, size_t len) {
    if (len == 0 || len > MAX_NAME || s[0] == '.' || strlen(s) != len)
        return 0;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (!((c >= 'a' && c <= 'z') ||
              (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') ||
              c == '.' || c == '_' || c == '-')) return 0;
    }
    return 1;
}
static int open_leaf(int root, const char *name) {
    /* Refuse existing leaves (including symlinks/hardlinks) rather than
     * truncating or following them. Not a whole-tree atomic protocol. */
    int fd = openat(root, name,
                    O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) die("destination leaf exists or is unsafe", -1);
    return fd;
}
static void publish_bytes(int root, const Item *item, const uint8_t *data) {
    int fd = open_leaf(root, item->name);
    write_all(fd, data, (size_t)item->size);
    if (close(fd) != 0) die("close leaf", -1);
}
static void stream_one(const CmpctArchive *archive, int root,
                       const Item *item, uint8_t *buffer) {
    int fd = open_leaf(root, item->name);
    uint64_t offset = 0;
    while (offset < item->size) {
        size_t wanted = (size_t)(item->size - offset < CHUNK ?
                                  item->size - offset : CHUNK);
        size_t received = 0;
        ok(cmpct_entry_read_range(archive, item->index, offset,
                                  buffer, wanted, &received), "stream range");
        if (received != wanted) die("short stream range", CMPCT_ERR_FORMAT);
        write_all(fd, buffer, received);
        offset += (uint64_t)received;
    }
    if (close(fd) != 0) die("close stream leaf", -1);
}

int main(int argc, char **argv) {
    if (argc != 3) die("usage: owner-bounded ARCHIVE DEST", 0);
    CmpctArchive *archive = NULL;
    ok(cmpct_open(argv[1], &archive), "archive open");
    size_t count = cmpct_entry_count(archive);
    if (count == 0 || count > MAX_ENTRIES) die("entry count budget", 0);
    Item *items = calloc(count, sizeof(*items));
    if (!items) die("entry metadata allocation", -1);
    size_t nf = 0;
    uint64_t total = 0;
    /* Preflight ALL names, size bounds and optional ownership before any
     * materialization. This narrows avoidable partially written-tree errors. */
    for (size_t i = 0; i < count; ++i) {
        CmpctEntryInfo info;
        ok(cmpct_entry_info(archive, i, &info), "entry info");
        if (info.kind != 0) continue;
        if (info.size > MAX_SINGLE || total > MAX_TOTAL - info.size)
            die("logical output budget", 0);
        total += info.size;
        Item *it = &items[nf++];
        it->index = i;
        it->size = info.size;
        size_t name_len = 0;
        ok(cmpct_entry_path(archive, i, NULL, 0, &name_len),
           "path length");
        if (name_len == 0 || name_len > MAX_NAME)
            die("path length budget", 0);
        memset(it->name, 0, sizeof(it->name));
        ok(cmpct_entry_path(archive, i, it->name, name_len + 1,
                            &name_len), "entry path");
        if (!safe_name(it->name, name_len)) die("root-only name", 0);
        size_t owner = SIZE_MAX;
        int rc = cmpct_entry_pack_owner(archive, i, &owner);
        if (rc == CMPCT_OK) {
            it->eligible = 1;
            it->owner = owner;
        } else if (rc != CMPCT_ERR_UNSUPPORTED && rc != CMPCT_ERR_LIMIT) {
            die("owner query failed", rc);
        }
    }
    int root = open(argv[2], O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (root < 0) die("destination root", -1);
    uint8_t *scratch = malloc(CHUNK);
    if (!scratch) die("range buffer allocation", -1);

    size_t batches = 0, grouped = 0, fallback = 0, max_stage = 0;
    /* One authenticated physical owner per operation and one staged batch
     * at a time. A truncated owner group is retried in another bounded call.
     * Never treat corrupt batch contents as an opportunity for RAW fallback. */
    for (size_t i = 0; i < nf; ++i) {
        if (items[i].done || !items[i].eligible || items[i].size == 0)
            continue;
        size_t ids[MAX_RANGES];
        size_t n = 0, bytes = 0;
        const size_t owner = items[i].owner;
        for (size_t j = i; j < nf; ++j) {
            Item *p = &items[j];
            if (p->done || !p->eligible || p->owner != owner ||
                p->size == 0 || p->size > MAX_BATCH - bytes)
                continue;
            if (n == MAX_RANGES) break;
            ids[n++] = j;
            bytes += (size_t)p->size;
        }
        if (n < 2) continue; /* Batch singleton is measured N=1 loss. */
        CmpctPackRange *requests = calloc(n, sizeof(*requests));
        uint8_t *stage = malloc(bytes ? bytes : 1);
        if (!requests || !stage) die("bounded batch allocation", -1);
        for (size_t k = 0; k < n; ++k) {
            Item *p = &items[ids[k]];
            requests[k] = (CmpctPackRange){p->index, 0, (size_t)p->size};
        }
        size_t out = 0;
        ok(cmpct_pack_read_batch(archive, requests, n, stage,
                                 bytes, &out), "SHA-verified owner batch");
        if (out != bytes) die("short owner batch", CMPCT_ERR_FORMAT);
        size_t from = 0;
        for (size_t k = 0; k < n; ++k) {
            Item *p = &items[ids[k]];
            publish_bytes(root, p, stage + from);
            from += (size_t)p->size;
            p->done = 1;
        }
        if (from != bytes) die("batch sum mismatch", CMPCT_ERR_FORMAT);
        if (bytes > max_stage) max_stage = bytes;
        batches++;
        grouped += n;
        free(stage);
        free(requests);
    }
    for (size_t i = 0; i < nf; ++i) {
        if (items[i].done) continue;
        stream_one(archive, root, &items[i], scratch);
        items[i].done = 1;
        fallback++;
    }
    if (close(root) != 0) die("close directory", -1);
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) != 0) die("rss", -1);
    printf("{\"mode\":\"owner_bounded\",\"members\":%zu,"
           "\"decoded_bytes\":%" PRIu64 ",\"batch_count\":%zu,"
           "\"batched_members\":%zu,\"fallback\":%zu,"
           "\"max_staging_bytes\":%zu,\"rss_kib\":%ld}\n",
           nf, total, batches, grouped, fallback, max_stage, ru.ru_maxrss);
    free(scratch);
    free(items);
    cmpct_close(archive);
    return 0;
}
