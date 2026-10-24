/* O19 research-only: add post-fsync staged-inode readback to O18's SHA barrier.
 * This is NOT a product extractor, generic filesystem implementation, or
 * externally authenticated source signature. Only a flat private POSIX root
 * and precommitted per-file logical SHA are supported. */
#define _POSIX_C_SOURCE 200809L
#include "native/cmpct-core/include/cmpct.h"
#include <openssl/evp.h>
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

#define O18_CHUNK (64U * 1024U)
#define O18_MAX_OUTPUT (4U * 1024U * 1024U)
#define O18_MAX_ENTRIES 512U
#define O18_MAX_NAME 95U
#define O18_STAGE ".cmpct-o18-stage"

static int valid_leaf(const char *name) {
    size_t n = strlen(name);
    if (!n || n > O18_MAX_NAME || name[0] == '.') return 0;
    for (size_t i = 0; i < n; i++) {
        unsigned char c = (unsigned char)name[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.'))
            return 0;
    }
    return 1;
}
static int root_is_empty(int root) {
    int scan = dup(root);
    if (scan < 0) return 0;
    DIR *dir = fdopendir(scan);
    if (!dir) { close(scan); return 0; }
    int ok = 1;
    struct dirent *dent;
    errno = 0;
    while ((dent = readdir(dir))) {
        if (strcmp(dent->d_name, ".") && strcmp(dent->d_name, "..")) {
            ok = 0;
            break;
        }
        errno = 0;
    }
    if (errno) ok = 0;
    if (closedir(dir)) ok = 0;
    return ok;
}
static int write_all(int fd, const uint8_t *data, size_t len) {
    while (len) {
        ssize_t n = write(fd, data, len);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        data += (size_t)n;
        len -= (size_t)n;
    }
    return 0;
}
static void print_digest(const uint8_t hash[32]) {
    for (size_t i = 0; i < 32; ++i) printf("%02x", hash[i]);
}
int main(int argc, char **argv) {
    /* rc=4: unsupported/missing commitment; rc=5: digest mismatch;
     * rc=6: safe destination rejected; rc=7: read/write/other failure. */
    if (argc != 4 || !valid_leaf(argc == 4 ? argv[3] : ""))
        return 2;
    int status = 7, root = -1, stage = -1, stage_created = 0;
    size_t found = SIZE_MAX;
    uint8_t indexed[32], observed[32], staged[32];
    uint8_t *scratch = NULL;
    CmpctArchive *archive = NULL;
    EVP_MD_CTX *sha_ctx = NULL;
    uint64_t file_size = 0;
    int rc = cmpct_open(argv[1], &archive);
    if (rc != CMPCT_OK || !archive) goto cleanup;
    size_t n = cmpct_entry_count(archive);
    if (!n || n > O18_MAX_ENTRIES) goto cleanup;
    for (size_t i = 0; i < n; ++i) {
        size_t path_len = 0;
        if (cmpct_entry_path(archive, i, NULL, 0, &path_len) != CMPCT_OK)
            goto cleanup;
        if (path_len != strlen(argv[3])) continue;
        char leaf[O18_MAX_NAME + 1];
        if (path_len > O18_MAX_NAME ||
            cmpct_entry_path(archive, i, leaf, path_len + 1, &path_len) != CMPCT_OK)
            goto cleanup;
        if (!strcmp(leaf, argv[3])) {
            if (found != SIZE_MAX) goto cleanup;
            found = i;
        }
    }
    if (found == SIZE_MAX) goto cleanup;
    CmpctEntryInfo info;
    if (cmpct_entry_info(archive, found, &info) != CMPCT_OK ||
        info.kind != 0 || info.size == 0 || info.size > O18_MAX_OUTPUT)
        goto cleanup;
    file_size = info.size;
    rc = cmpct_entry_logical_sha256(archive, found, indexed);
    if (rc == CMPCT_ERR_UNSUPPORTED) { status = 4; goto cleanup; }
    if (rc != CMPCT_OK) goto cleanup;

    root = open(argv[2], O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (root < 0 || !root_is_empty(root)) { status = 6; goto cleanup; }
    stage = openat(root, O18_STAGE,
                   O_RDWR | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (stage < 0) { status = 6; goto cleanup; }
    stage_created = 1;
    scratch = malloc(O18_CHUNK);
    sha_ctx = EVP_MD_CTX_new();
    if (!scratch || !sha_ctx ||
        EVP_DigestInit_ex(sha_ctx, EVP_sha256(), NULL) != 1) goto cleanup;
    for (uint64_t off = 0; off < file_size; ) {
        size_t want = (size_t)(file_size - off < O18_CHUNK ?
                               file_size - off : O18_CHUNK);
        size_t got = SIZE_MAX;
        rc = cmpct_entry_read_range(archive, found, off, scratch, want, &got);
        if (rc != CMPCT_OK || got != want ||
            EVP_DigestUpdate(sha_ctx, scratch, got) != 1 ||
            write_all(stage, scratch, got)) goto cleanup;
        off += got;
    }
    unsigned int hash_length = 0;
    if (EVP_DigestFinal_ex(sha_ctx, observed, &hash_length) != 1 ||
        hash_length != 32U || fsync(stage)) goto cleanup;
    if (memcmp(indexed, observed, sizeof(indexed))) {
        status = 5;
        goto cleanup;
    }
    /* A write() success and fsync() do not prove bytes persisted as supplied.
     * Authenticate the actual stage inode with one bounded readback pass.
     * This catches corruption occurring before the readback, NOT a concurrent
     * mutator acting between the readback and linkat(). */
    if (lseek(stage, 0, SEEK_SET) < 0 ||
        EVP_DigestInit_ex(sha_ctx, EVP_sha256(), NULL) != 1) goto cleanup;
    for (uint64_t off = 0; off < file_size; ) {
        size_t want = (size_t)(file_size - off < O18_CHUNK ?
                               file_size - off : O18_CHUNK);
        ssize_t got = read(stage, scratch, want);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0 || EVP_DigestUpdate(sha_ctx, scratch, (size_t)got) != 1)
            goto cleanup;
        off += (uint64_t)got;
    }
    hash_length = 0;
    if (EVP_DigestFinal_ex(sha_ctx, staged, &hash_length) != 1 ||
        hash_length != 32U) goto cleanup;
    if (memcmp(indexed, staged, sizeof(indexed))) {
        status = 5;
        goto cleanup;
    }
    if (close(stage)) { stage = -1; goto cleanup; }
    stage = -1;
    /* linkat with no replace is the publication gate. The staged inode is
     * never visible under the requested final name until digest equality.
     * The stage basename itself exists transiently in this private root. */
    if (linkat(root, O18_STAGE, root, argv[3], 0)) {
        status = 6;
        goto cleanup;
    }
    status = 0;
    printf("{\"decision\":\"VERIFIED_CDC_STAGED\",\"bytes\":%" PRIu64
           ",\"chunk_bytes\":%u,\"sha256\":\"",
           file_size, O18_CHUNK);
    print_digest(observed);
    printf("\"}\n");
cleanup:
    if (stage >= 0 && close(stage)) status = 7;
    if (stage_created && root >= 0 &&
        unlinkat(root, O18_STAGE, 0) && status == 0) status = 7;
    if (root >= 0 && close(root) && status == 0) status = 7;
    EVP_MD_CTX_free(sha_ctx);
    free(scratch);
    if (archive) cmpct_close(archive);
    if (status) fprintf(stderr, "O19_REJECT status=%d native_rc=%d\n", status, rc);
    return status;
}
