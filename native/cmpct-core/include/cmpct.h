#ifndef CMPCT_CORE_H
#define CMPCT_CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct CmpctArchive CmpctArchive;
typedef struct CmpctStream CmpctStream;

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
 * Footnote: the ABI remains read-oriented, but it is no longer range-only. The same opaque native
 * parser now owns structural preflight, committed-generation recovery, sequential member streams and
 * safe extraction. Platform packages therefore do not need private format parsing merely to browse or
 * materialize an archive, and unsupported semantics still fail through one typed status boundary.
 */
int32_t cmpct_open(const char *path, CmpctArchive **out);
void cmpct_close(CmpctArchive *archive);
uint16_t cmpct_revision(const CmpctArchive *archive);
size_t cmpct_entry_count(const CmpctArchive *archive);
int32_t cmpct_entry_info(const CmpctArchive *archive, size_t index, CmpctEntryInfo *out);
int32_t cmpct_entry_path(const CmpctArchive *archive, size_t index, char *buffer, size_t capacity, size_t *out_len);

/* Validate the complete authenticated logical structure plus physical blob framing without extraction. */
int32_t cmpct_preflight(const CmpctArchive *archive);

/*
 * Read exactly `length` bytes from one logical entry beginning at `offset`.
 * `out_read` receives `length` on success and zero on failure. A zero-length request may pass
 * `buffer == NULL`. Resource/work limits return CMPCT_ERR_LIMIT rather than overcommitting memory.
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
 * Open/read/close a sequential logical-member stream. The archive handle must outlive every stream
 * created from it. EOF is reported as CMPCT_OK with `out_read == 0`.
 *
 * Footnote: this stream intentionally delegates to the same range/integrity machinery instead of
 * exposing codec-specific state through the public ABI. That keeps Android/desktop clients stable as
 * internal decode strategies become more incremental over time.
 */
int32_t cmpct_entry_stream_open(
    const CmpctArchive *archive,
    size_t index,
    CmpctStream **out
);
int32_t cmpct_stream_read(
    CmpctStream *stream,
    uint8_t *buffer,
    size_t capacity,
    size_t *out_read
);
void cmpct_stream_close(CmpctStream *stream);

/*
 * Extract the complete logical tree into an absent or empty UTF-8 destination directory.
 * The native extractor preflights first, refuses lexical/path escape, verifies supported payload
 * integrity through the shared reader, and materializes hardlinks only after their final target.
 */
int32_t cmpct_extract_all(const CmpctArchive *archive, const char *destination);

#ifdef __cplusplus
}
#endif

#endif
