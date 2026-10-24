/* O15: source-exact public C ABI flat POSIX tree/inode topology research client.
 * NOT a production extractor: no concurrent destination adversary, no rollback,
 * no nested names, metadata/xattr fidelity, portable API, or RAW mutation proof.
 * The private Rust index parser and ABI remain the sole archive trust boundary.
 */
#define _POSIX_C_SOURCE 200809L
#include "native/cmpct-core/include/cmpct.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define O15_MAX_ENTRIES 512U
#define O15_MAX_NAME 95U
#define O15_MAX_SINGLE (4U * 1024U * 1024U)
#define O15_MAX_TOTAL (16U * 1024U * 1024U)
#define O15_MAX_BATCH (1024U * 1024U)
#define O15_CHUNK (64U * 1024U)
#define O15_MAX_RANGES 512U

typedef struct Entry {
    uint8_t kind;
    uint64_t size;
    size_t index, link_owner, pack_owner;
    int pack_eligible, done;
    char name[O15_MAX_NAME + 1];
    char symlink_target[O15_MAX_NAME + 1];
} Entry;

static void fatal(const char *why, int code) {
    fprintf(stderr, "O15_FAIL %s rc=%d errno=%d\n", why, code, errno);
    exit(3);
}
static void require_ok(int rc, const char *name) {
    if (rc != CMPCT_OK) fatal(name, rc);
}
static int valid_flat(const char *name, size_t n) {
    if (!n || n > O15_MAX_NAME || name[0] == '.' ||
        strlen(name) != n) return 0;
    for (size_t k = 0; k < n; ++k) {
        unsigned char c = (unsigned char)name[k];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || (c >= '0' && c <= '9') ||
              c == '_' || c == '-' || c == '.')) return 0;
    }
    return 1;
}
static void write_all(int fd, const uint8_t *data, size_t len) {
    while (len) {
        ssize_t written = write(fd, data, len);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) fatal("write", -1);
        data += (size_t)written;
        len -= (size_t)written;
    }
}
static int new_leaf(int root, const char *name) {
    int fd = openat(root, name, O_WRONLY | O_CREAT | O_EXCL |
                   O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) fatal("create leaf", -1);
    return fd;
}
static void emit_bytes(int root, const Entry *entry, const uint8_t *data) {
    int fd = new_leaf(root, entry->name);
    write_all(fd, data, (size_t)entry->size);
    if (close(fd)) fatal("close leaf", -1);
}
static void emit_scalar(const CmpctArchive *archive, int root,
                        const Entry *entry, uint8_t *scratch) {
    int fd = new_leaf(root, entry->name);
    uint64_t off = 0;
    while (off < entry->size) {
        size_t want = (size_t)(entry->size - off < O15_CHUNK ?
                               entry->size - off : O15_CHUNK);
        size_t received = SIZE_MAX;
        require_ok(cmpct_entry_read_range(archive, entry->index, off,
                                          scratch, want, &received),
                   "range read");
        if (received != want) fatal("short range", -3);
        write_all(fd, scratch, received);
        off += received;
    }
    if (close(fd)) fatal("close scalar", -1);
}
static void reject_nonempty_root(int root) {
    int scan = dup(root);
    if (scan < 0) fatal("dup root", -1);
    DIR *dir = fdopendir(scan);
    if (!dir) fatal("fdopendir root", -1);
    struct dirent *dent;
    errno = 0;
    while ((dent = readdir(dir)) != NULL) {
        if (strcmp(dent->d_name, ".") && strcmp(dent->d_name, ".."))
            fatal("destination not empty (preflight)", -1);
        errno = 0;
    }
    if (errno) fatal("readdir", -1);
    if (closedir(dir)) fatal("closedir", -1);
}

int main(int argc, char **argv) {
    if (argc != 3) fatal("usage: O15 ARCHIVE EMPTY_DEST", 0);
    CmpctArchive *archive = NULL;
    require_ok(cmpct_open(argv[1], &archive), "open archive");
    size_t n = cmpct_entry_count(archive);
    if (!n || n > O15_MAX_ENTRIES) fatal("entry count bound", -4);
    Entry *entries = calloc(n, sizeof(*entries));
    if (!entries) fatal("entry metadata allocation", -1);
    uint64_t logical_total = 0;
    size_t regular = 0, hardlinks = 0, symlinks = 0;
    /* Source and graph metadata must be completely checked BEFORE output. */
    for (size_t i = 0; i < n; ++i) {
        Entry *ent = &entries[i];
        ent->index = i;
        CmpctEntryInfo info;
        require_ok(cmpct_entry_info(archive, i, &info), "entry info");
        if (info.kind != 0 && info.kind != 2 && info.kind != 3)
            fatal("unsupported kind: flat files only", -7);
        ent->kind = info.kind;
        ent->size = info.size;
        if (info.size > O15_MAX_SINGLE ||
            logical_total > O15_MAX_TOTAL - info.size)
            fatal("logical budget", -4);
        logical_total += info.size;
        size_t name_len = 0;
        require_ok(cmpct_entry_path(archive, i, NULL, 0, &name_len),
                   "path query");
        if (!name_len || name_len > O15_MAX_NAME)
            fatal("path bound", -4);
        require_ok(cmpct_entry_path(archive, i, ent->name, name_len + 1,
                                    &name_len), "path copy");
        if (!valid_flat(ent->name, name_len)) fatal("unsafe flat name", -3);
        for (size_t j = 0; j < i; ++j) {
            if (!strcmp(entries[j].name, ent->name))
                fatal("duplicate leaf", -3);
        }
        if (ent->kind == 0) {
            regular++;
            size_t pack_owner = SIZE_MAX;
            int rc = cmpct_entry_pack_owner(archive, i, &pack_owner);
            if (rc == CMPCT_OK) {
                ent->pack_eligible = 1;
                ent->pack_owner = pack_owner;
            } else if (rc != CMPCT_ERR_UNSUPPORTED && rc != CMPCT_ERR_LIMIT) {
                fatal("PACK query", rc);
            }
        } else if (ent->kind == 2) {
            symlinks++;
            if (!ent->size || ent->size > O15_MAX_NAME)
                fatal("symlink target bound", -4);
            size_t got = SIZE_MAX;
            require_ok(cmpct_entry_read_range(archive, i, 0,
                       (uint8_t *)ent->symlink_target, (size_t)ent->size,
                       &got), "symlink target read");
            if (got != ent->size) fatal("short symlink target", -3);
            ent->symlink_target[got] = '\0';
            if (!valid_flat(ent->symlink_target, got))
                fatal("symlink target unsafe", -3);
        } else {
            hardlinks++;
            ent->link_owner = SIZE_MAX;
            require_ok(cmpct_entry_hardlink_owner(archive, i, &ent->link_owner),
                       "hardlink owner");
        }
    }
    /* The ordinal is validated by Rust, but the client still enforces its
     * own publication constraints, including owner kind and flat namespace. */
    for (size_t i = 0; i < n; ++i) {
        Entry *e = &entries[i];
        if (e->kind == 3) {
            if (e->link_owner >= n || entries[e->link_owner].kind != 0 ||
                e->size != entries[e->link_owner].size)
                fatal("invalid terminal link owner", -3);
        }
        if (e->kind == 2) {
            int found = 0;
            for (size_t j = 0; j < n; ++j)
                if (entries[j].kind == 0 &&
                    !strcmp(e->symlink_target, entries[j].name)) found = 1;
            if (!found) fatal("unresolved symlink", -3);
        }
    }
    int root = open(argv[2], O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (root < 0) fatal("destination root", -1);
    reject_nonempty_root(root);
    uint8_t *scratch = malloc(O15_CHUNK);
    if (!scratch) fatal("scratch allocation", -1);
    size_t batch_calls = 0, batch_members = 0, fallback = 0, max_stage = 0;
    /* Group only matching physical Zstd owners. One live stage per call. */
    for (size_t i = 0; i < n; ++i) {
        if (entries[i].kind || !entries[i].pack_eligible || entries[i].done ||
            entries[i].size == 0) continue;
        size_t ids[O15_MAX_RANGES], count = 0, total = 0;
        for (size_t j = i; j < n; ++j) {
            Entry *p = &entries[j];
            if (p->kind || p->done || !p->pack_eligible ||
                p->pack_owner != entries[i].pack_owner ||
                p->size == 0 || p->size > O15_MAX_BATCH - total) continue;
            if (count == O15_MAX_RANGES) break;
            ids[count++] = j;
            total += (size_t)p->size;
        }
        if (count < 2) continue;
        CmpctPackRange *req = calloc(count, sizeof(*req));
        uint8_t *stage = malloc(total);
        if (!req || !stage) fatal("staging allocation", -1);
        for (size_t k = 0; k < count; ++k) {
            Entry *p = &entries[ids[k]];
            req[k] = (CmpctPackRange){p->index, 0, (size_t)p->size};
        }
        size_t obtained = SIZE_MAX;
        require_ok(cmpct_pack_read_batch(archive, req, count, stage,
                                          total, &obtained),
                   "verified PACK batch");
        if (obtained != total) fatal("short PACK batch", -3);
        size_t off = 0;
        for (size_t k = 0; k < count; ++k) {
            Entry *p = &entries[ids[k]];
            emit_bytes(root, p, stage + off);
            off += (size_t)p->size;
            p->done = 1;
        }
        if (off != obtained) fatal("stage accounting", -3);
        if (total > max_stage) max_stage = total;
        batch_calls++;
        batch_members += count;
        free(stage);
        free(req);
    }
    for (size_t i = 0; i < n; ++i) {
        Entry *p = &entries[i];
        if (p->kind || p->done) continue;
        emit_scalar(archive, root, p, scratch);
        p->done = 1;
        fallback++;
    }
    /* All regular owners exist before any aliases, regardless of index sort. */
    for (size_t i = 0; i < n; ++i) {
        Entry *p = &entries[i];
        if (p->kind == 3 &&
            linkat(root, entries[p->link_owner].name, root, p->name, 0))
            fatal("publish hardlink", -1);
    }
    for (size_t i = 0; i < n; ++i) {
        Entry *p = &entries[i];
        if (p->kind == 2 && symlinkat(p->symlink_target, root, p->name))
            fatal("publish symlink", -1);
    }
    if (close(root)) fatal("close root", -1);
    printf("{\"regular\":%zu,\"hardlinks\":%zu,\"symlinks\":%zu,"
           "\"batch_calls\":%zu,\"batch_members\":%zu,\"fallback\":%zu,"
           "\"max_stage_bytes\":%zu,\"logical_budget\":%" PRIu64 "}\n",
           regular, hardlinks, symlinks, batch_calls, batch_members,
           fallback, max_stage, logical_total);
    free(scratch);
    free(entries);
    cmpct_close(archive);
    return 0;
}
