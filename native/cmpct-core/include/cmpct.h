#ifndef CMPCT_CORE_H
#define CMPCT_CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct CmpctArchive CmpctArchive;

typedef enum CmpctStatus {
    CMPCT_OK = 0,
    CMPCT_ERR_NULL = -1,
    CMPCT_ERR_IO = -2,
    CMPCT_ERR_FORMAT = -3,
    CMPCT_ERR_LIMIT = -4,
    CMPCT_ERR_UTF8 = -5,
    CMPCT_ERR_RANGE = -6,
    CMPCT_ERR_UNSUPPORTED = -7,
    CMPCT_ERR_PANIC = -127
} CmpctStatus;

typedef struct CmpctEntryInfo {
    uint8_t kind;
    uint8_t reserved[3];
    uint32_t mode;
    uint64_t size;
    int64_t mtime_ns;
} CmpctEntryInfo;

/*
 * Footnote: this ABI is intentionally read-only. Platform packages may identify, enumerate and
 * range-read archives without embedding Python while the representation-complete native reader is
 * still being hardened. The opaque handle prevents Android/Windows/Apple/Linux clients from
 * depending on Rust-internal layout, and unsupported storage kinds fail explicitly rather than being
 * guessed by platform code.
 */
int32_t cmpct_open(const char *path, CmpctArchive **out);
void cmpct_close(CmpctArchive *archive);
uint16_t cmpct_revision(const CmpctArchive *archive);
size_t cmpct_entry_count(const CmpctArchive *archive);
int32_t cmpct_entry_info(const CmpctArchive *archive, size_t index, CmpctEntryInfo *out);
int32_t cmpct_entry_path(const CmpctArchive *archive, size_t index, char *buffer, size_t capacity, size_t *out_len);

/*
 * Read at most `length` bytes from one logical entry beginning at `offset`.
 * `out_read` receives the number of bytes copied. A zero-length request may pass `buffer == NULL`.
 * Footnote: this declaration intentionally mirrors the already-exported Rust symbol so JNI/desktop
 * consumers compile against the same ABI that conformance tests exercise instead of carrying private
 * function prototypes that can silently drift.
 */
int32_t cmpct_entry_read_range(
    const CmpctArchive *archive,
    size_t index,
    uint64_t offset,
    uint8_t *buffer,
    size_t length,
    size_t *out_read
);

/*
 * Explicit operation-scoped, verified batch read of ranges from ONE physical
 * Zstd S_PACK. The output is all requested ranges concatenated in order.
 * This optional export leaves independent cmpct_entry_read_range semantics
 * unchanged and does not retain decoded data between calls.
 *
 * Bounds: 1..1024 requests, <=16 MiB total output, <=16 MiB compressed and
 * decoded physical pack. RAW, mixed physical owners and malformed ranges
 * fail closed. On error *out_read=0 and the output buffer is not modified.
 * Requests, buffer and out_read must be valid, pairwise nonoverlapping memory;
 * archive must remain live for the entire call.
 */
typedef struct CmpctPackRange {
    size_t entry_index;
    uint64_t offset;
    size_t length;
} CmpctPackRange;

int32_t cmpct_pack_read_batch(
    const CmpctArchive *archive,
    const CmpctPackRange *requests,
    size_t count,
    uint8_t *buffer,
    size_t capacity,
    size_t *out_read
);

#ifdef __cplusplus
}
#endif

#endif
