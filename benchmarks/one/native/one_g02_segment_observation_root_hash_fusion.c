#include <stddef.h>
#include <stdint.h>
#include <openssl/evp.h>

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind;
} one_g02_fused_segment;

typedef struct {
    uint64_t compared_target_bytes;
    uint64_t segments;
} one_g02_fused_segment_stats;

/* Existing exact authorities, linked into the same shared object. */
int one_g02_segment_plan_one_pass(const uint8_t *src, const uint8_t *dst, size_t n,
                                  one_g02_fused_segment *out, size_t cap,
                                  one_g02_fused_segment_stats *stats);
int one_g02_hash_target_whole(const uint8_t *target, size_t target_len, uint8_t out[32]);

#define ONE_G02_HASH_BLOCK (16u * 1024u)

static int fused_is_ref_byte(const uint8_t *src, const uint8_t *dst, size_t i) {
    return i > 0u && dst[i] == src[i - 1u];
}

int one_g02_segment_then_hash_baseline(
    const uint8_t *src, const uint8_t *dst, size_t n,
    one_g02_fused_segment *out, size_t cap,
    one_g02_fused_segment_stats *stats, uint8_t digest[32])
{
    int rc = one_g02_segment_plan_one_pass(src, dst, n, out, cap, stats);
    if (rc != 0) return rc;
    rc = one_g02_hash_target_whole(dst, n, digest);
    return rc == 0 ? 0 : -20;
}

int one_g02_segment_and_hash_fixed_blocks(
    const uint8_t *src, const uint8_t *dst, size_t n,
    one_g02_fused_segment *out, size_t cap,
    one_g02_fused_segment_stats *stats, uint8_t digest[32])
{
    if (!src || !dst || !stats || !digest) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0u;

    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx) return -2;
    if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1) {
        EVP_MD_CTX_free(ctx);
        return -3;
    }

    size_t hash_off = 0u;
    size_t i = 0u;
    while (i < n) {
        const int ref = fused_is_ref_byte(src, dst, i);
        const size_t begin = i++;
        while (i < n && fused_is_ref_byte(src, dst, i) == ref) ++i;
        const size_t len = i - begin;
        const size_t idx = (size_t)stats->segments++;
        if (!out || idx >= cap || begin > UINT32_MAX || len > UINT32_MAX) {
            EVP_MD_CTX_free(ctx);
            return -4;
        }
        out[idx].kind = ref ? 0u : 1u;
        out[idx].start = (uint32_t)(ref ? begin - 1u : begin);
        out[idx].length = (uint32_t)len;

        /* Regular SHA boundaries: independent of the number of emitted Segments. */
        while (i - hash_off >= (size_t)ONE_G02_HASH_BLOCK) {
            if (EVP_DigestUpdate(ctx, dst + hash_off, (size_t)ONE_G02_HASH_BLOCK) != 1) {
                EVP_MD_CTX_free(ctx);
                return -5;
            }
            hash_off += (size_t)ONE_G02_HASH_BLOCK;
        }
    }

    if (hash_off < n && EVP_DigestUpdate(ctx, dst + hash_off, n - hash_off) != 1) {
        EVP_MD_CTX_free(ctx);
        return -6;
    }
    unsigned int digest_len = 0u;
    const int ok = EVP_DigestFinal_ex(ctx, digest, &digest_len);
    EVP_MD_CTX_free(ctx);
    return (ok == 1 && digest_len == 32u) ? 0 : -7;
}
