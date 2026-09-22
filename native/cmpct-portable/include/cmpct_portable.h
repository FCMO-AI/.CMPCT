#ifndef CMPCT_PORTABLE_H
#define CMPCT_PORTABLE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Shared CMPCT portable-reader ABI.
 *
 * Footnote: this ABI is additive to native/cmpct-core/include/cmpct.h. The mature
 * revision-24 ABI remains untouched; this surface dispatches genuine r24 plus the
 * canonical revision-25 profiles while keeping research CMPNX identities at
 * revision 0 so experimental bytes cannot masquerade as a release archive.
 */

typedef struct PortableArchive PortableArchive;

typedef enum CmpctPortableStatus {
    CMPCT_PORTABLE_OK = 0,
    CMPCT_PORTABLE_NULL = -1,
    CMPCT_PORTABLE_IO = -2,
    CMPCT_PORTABLE_FORMAT = -3,
    CMPCT_PORTABLE_LIMIT = -4,
    CMPCT_PORTABLE_UTF8 = -5,
    CMPCT_PORTABLE_RANGE = -6,
    CMPCT_PORTABLE_UNSUPPORTED = -7,
    CMPCT_PORTABLE_INTEGRITY = -8,
    CMPCT_PORTABLE_PANIC = -127,
} CmpctPortableStatus;

typedef struct CmpctPortableEntryInfo {
    uint8_t kind;
    uint8_t reserved[3];
    uint32_t mode;
    uint64_t size;
    int64_t mtime_ns;
} CmpctPortableEntryInfo;

typedef struct CmpctPortableMemberStats {
    uint64_t logical_bytes;
    uint64_t decoded_context_bytes;
    double amplification;
} CmpctPortableMemberStats;

int32_t cmpct_portable_open(const char *path, PortableArchive **out_archive);
void cmpct_portable_close(PortableArchive *archive);

/* Returns 24 or 25 for release archives; research-only CMPNX profiles return 0. */
int32_t cmpct_portable_revision(const PortableArchive *archive, uint32_t *out_revision);
int32_t cmpct_portable_entry_count(const PortableArchive *archive, size_t *out_count);
int32_t cmpct_portable_entry_info(
    const PortableArchive *archive,
    size_t index,
    CmpctPortableEntryInfo *out_info);

/*
 * If buffer is NULL, entry_path reports the exact UTF-8 byte length via required.
 * No NUL terminator is included in required or written by the function.
 */
int32_t cmpct_portable_entry_path(
    const PortableArchive *archive,
    size_t index,
    uint8_t *buffer,
    size_t capacity,
    size_t *required);

/*
 * Bounded logical range read. r24 delegates to cmpct-core's exact range reader;
 * r25 authenticates the complete selected member and copies only the requested
 * window because the v0.30 release locality contract is member-selective.
 */
int32_t cmpct_portable_entry_read_range(
    const PortableArchive *archive,
    size_t index,
    uint64_t offset,
    uint8_t *buffer,
    size_t capacity,
    size_t *written);

/* Whole-member convenience read; large r25 members should use range/streaming CLI. */
int32_t cmpct_portable_entry_read(
    const PortableArchive *archive,
    size_t index,
    uint8_t *buffer,
    size_t capacity,
    size_t *written,
    CmpctPortableMemberStats *stats);

/* Performs profile-specific integrity/tree verification. */
int32_t cmpct_portable_verify(const PortableArchive *archive);

#ifdef __cplusplus
}
#endif

#endif /* CMPCT_PORTABLE_H */
