/* O7: test-only public C ABI client. All archive parsing stays in shared Rust core.
 * Root-level fixture is intentional: this is a selective read / grouping cost
 * court, not a replacement filesystem extraction engine or a shipping CLI.
 */
#define _POSIX_C_SOURCE 200809L
#include "native/cmpct-core/include/cmpct.h"
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>

#define MAX_MEMBER (16U * 1024U * 1024U)
#define MAX_REQUESTS 1024U

typedef struct Item {
    char *name;
    size_t archive_index;
    size_t length;
    size_t owner;
    int eligible;
    int done;
    unsigned char *bytes;
} Item;

static void fail(const char *why, int status) {
    fprintf(stderr, "O7_FAIL %s status=%d errno=%d\n", why, status, errno);
    exit(3);
}

static void check(int status, const char *why) {
    if (status != CMPCT_OK) fail(why, status);
}

static void independent_read(const CmpctArchive *archive, Item *item) {
    size_t actual = 0;
    check(cmpct_entry_read_range(archive, item->archive_index, 0, item->bytes,
                                 item->length, &actual), "per-entry read");
    if (actual != item->length) fail("per-entry short read", CMPCT_ERR_FORMAT);
    item->done = 1;
}

int main(int argc, char **argv) {
    if (argc != 4 || (strcmp(argv[3], "serial") != 0 && strcmp(argv[3], "group") != 0))
        fail("usage: consumer ARCHIVE DEST {serial|group}", 0);
    const int grouped = strcmp(argv[3], "group") == 0;
    CmpctArchive *archive = NULL;
    check(cmpct_open(argv[1], &archive), "archive open");
    size_t cap = cmpct_entry_count(archive);
    if (cap == 0 || cap > 4096) fail("unexpected fixture entry count", 0);
    Item *files = calloc(cap, sizeof(*files));
    if (!files) fail("item storage allocation", 0);
    size_t nf = 0;
    size_t decoded_bytes = 0;
    size_t fallback = 0, batches = 0, batched_files = 0;
    for (size_t i = 0; i < cap; ++i) {
        CmpctEntryInfo info;
        check(cmpct_entry_info(archive, i, &info), "entry info");
        if (info.kind != 0) continue;
        if (info.size > MAX_MEMBER) fail("fixture member exceeds memory budget", 0);
        size_t name_len = 0;
        check(cmpct_entry_path(archive, i, NULL, 0, &name_len), "entry name length");
        if (name_len == 0 || name_len > 200) fail("fixture name length", 0);
        char *name = calloc(name_len + 1, 1);
        if (!name) fail("path allocation", 0);
        check(cmpct_entry_path(archive, i, name, name_len + 1, &name_len),
              "entry name");
        // Fixture is root-only. Refuse arbitrary path traversal instead of
        // disguising this test client as a secure general filesystem extractor.
        if (name[0] == '.' || strchr(name, '/') || strchr(name, '\\'))
            fail("fixture must use safe root-level file paths", 0);
        Item *p = &files[nf++];
        p->name = name;
        p->archive_index = i;
        p->length = (size_t)info.size;
        p->bytes = malloc(p->length ? p->length : 1);
        if (!p->bytes) fail("member allocation", 0);
        decoded_bytes += p->length;
        if (grouped) {
            size_t owner = SIZE_MAX;
            int rc = cmpct_entry_pack_owner(archive, i, &owner);
            if (rc == CMPCT_OK) {
                p->eligible = 1;
                p->owner = owner;
            } else if (rc != CMPCT_ERR_UNSUPPORTED) {
                fail("pack owner query", rc);
            }
        }
    }

    if (grouped) {
        for (size_t i = 0; i < nf; ++i) {
            if (!files[i].eligible || files[i].done) continue;
            size_t owner = files[i].owner;
            size_t group_ids[MAX_REQUESTS];
            size_t n = 0, bytes_total = 0;
            for (size_t j = i; j < nf; ++j) {
                if (!files[j].done && files[j].eligible && files[j].owner == owner) {
                    if (n == MAX_REQUESTS || files[j].length > MAX_MEMBER - bytes_total)
                        fail("fixture grouped PACK exceeds declared batch budget", 0);
                    group_ids[n++] = j;
                    bytes_total += files[j].length;
                }
            }
            if (n < 2) continue; // Singleton is the measured negative batch regime.
            CmpctPackRange *ranges = calloc(n, sizeof(*ranges));
            unsigned char *all = malloc(bytes_total ? bytes_total : 1);
            if (!ranges || !all) fail("batch allocation", 0);
            for (size_t j = 0; j < n; ++j) {
                Item *p = &files[group_ids[j]];
                ranges[j] = (CmpctPackRange){p->archive_index, 0, p->length};
            }
            size_t read_count = 0;
            check(cmpct_pack_read_batch(archive, ranges, n, all, bytes_total,
                                        &read_count), "verified grouped read");
            if (read_count != bytes_total) fail("group read length", 0);
            size_t from = 0;
            for (size_t j = 0; j < n; ++j) {
                Item *p = &files[group_ids[j]];
                memcpy(p->bytes, all + from, p->length);
                from += p->length;
                p->done = 1;
            }
            free(ranges);
            free(all);
            ++batches;
            batched_files += n;
        }
    }
    for (size_t j = 0; j < nf; ++j) {
        if (!files[j].done) {
            independent_read(archive, &files[j]);
            ++fallback;
        }
    }

    // Same destination/materialization semantics for BOTH native read strategies.
    for (size_t i = 0; i < nf; ++i) {
        size_t len = strlen(argv[2]) + strlen(files[i].name) + 2;
        char *path = malloc(len);
        if (!path) fail("output path allocation", 0);
        snprintf(path, len, "%s/%s", argv[2], files[i].name);
        FILE *f = fopen(path, "wb");
        if (!f) fail("create extracted file", 0);
        if (fwrite(files[i].bytes, 1, files[i].length, f) != files[i].length)
            fail("write extracted file", 0);
        if (fclose(f) != 0) fail("close extracted file", 0);
        free(path);
    }
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) != 0) fail("getrusage", 0);
    printf("{\"mode\":\"%s\",\"members\":%zu,\"decoded_bytes\":%zu,"
           "\"batch_count\":%zu,\"batched_members\":%zu,\"fallback\":%zu,"
           "\"rss_kib\":%ld}\n",
           grouped ? "group" : "serial", nf, decoded_bytes,
           batches, batched_files, fallback, usage.ru_maxrss);
    for (size_t j = 0; j < nf; ++j) {
        free(files[j].name);
        free(files[j].bytes);
    }
    free(files);
    cmpct_close(archive);
    return 0;
}
