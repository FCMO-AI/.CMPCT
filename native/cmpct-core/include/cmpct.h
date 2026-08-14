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
 * Footnote: this ABI is intentionally read-only and index-focused first. Platform packages may use it
 * to identify and enumerate archives without embedding Python, while blob streaming/extraction is
 * added behind conformance tests. The opaque handle prevents Android/Windows/Apple/Linux clients from
 * depending on Rust-internal layout.
 */
int32_t cmpct_open(const char *path, CmpctArchive **out);
void cmpct_close(CmpctArchive *archive);
uint16_t cmpct_revision(const CmpctArchive *archive);
size_t cmpct_entry_count(const CmpctArchive *archive);
int32_t cmpct_entry_info(const CmpctArchive *archive, size_t index, CmpctEntryInfo *out);
int32_t cmpct_entry_path(const CmpctArchive *archive, size_t index, char *buffer, size_t capacity, size_t *out_len);

#ifdef __cplusplus
}
#endif

#endif
