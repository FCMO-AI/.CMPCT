#ifndef CMPCT_CODEC_H
#define CMPCT_CODEC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Encoding/decoding boundary for the package-owned codec engine.
 *
 * This header is intentionally separate from cmpct.h: cmpct.h remains the read-only archive/platform
 * ABI.  All buffers here are owned by the caller; CMPCT never returns an allocation across this ABI.
 * Status values use the existing CmpctStatus numeric contract: 0 OK, -1 null, -3 malformed codec
 * input, -6 insufficient/range, -127 contained panic.
 */

size_t cmpct_codec_zstd_compress_bound(size_t input_len);

int cmpct_codec_zstd_compress(
    const uint8_t *input, size_t input_len, int level,
    uint8_t *output, size_t output_capacity, size_t *output_len);

int cmpct_codec_zstd_compress_using_dict(
    const uint8_t *input, size_t input_len,
    const uint8_t *dictionary, size_t dictionary_len, int level,
    uint8_t *output, size_t output_capacity, size_t *output_len);

int cmpct_codec_zstd_decompress(
    const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity, size_t *output_len);

int cmpct_codec_zstd_decompress_using_dict(
    const uint8_t *input, size_t input_len,
    const uint8_t *dictionary, size_t dictionary_len,
    uint8_t *output, size_t output_capacity, size_t *output_len);

#ifdef __cplusplus
}
#endif

#endif /* CMPCT_CODEC_H */
