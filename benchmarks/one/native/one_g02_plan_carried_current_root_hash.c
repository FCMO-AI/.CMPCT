#include <stddef.h>
#include <stdint.h>
#include <openssl/evp.h>

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind; /* 0 = Ref(source), 1 = Surprise(target) */
} one_g02_hash_segment;

static int digest_begin(EVP_MD_CTX **ctx) {
    *ctx = EVP_MD_CTX_new();
    if (!*ctx) return -1;
    if (EVP_DigestInit_ex(*ctx, EVP_sha256(), NULL) != 1) {
        EVP_MD_CTX_free(*ctx);
        *ctx = NULL;
        return -2;
    }
    return 0;
}

static int digest_end(EVP_MD_CTX *ctx, uint8_t out[32]) {
    unsigned int n = 0;
    int ok = EVP_DigestFinal_ex(ctx, out, &n);
    EVP_MD_CTX_free(ctx);
    return (ok == 1 && n == 32u) ? 0 : -1;
}

int one_g02_hash_target_whole(const uint8_t *target, size_t target_len, uint8_t out[32]) {
    if ((!target && target_len) || !out) return -1;
    EVP_MD_CTX *ctx = NULL;
    if (digest_begin(&ctx) != 0) return -2;
    if (target_len && EVP_DigestUpdate(ctx, target, target_len) != 1) {
        EVP_MD_CTX_free(ctx);
        return -3;
    }
    return digest_end(ctx, out) == 0 ? 0 : -4;
}

int one_g02_hash_current_from_plan(
    const uint8_t *source, size_t source_len,
    const uint8_t *target, size_t target_len,
    const one_g02_hash_segment *segments, size_t segment_count,
    uint8_t out[32])
{
    if ((!source && source_len) || (!target && target_len) || (!segments && segment_count) || !out)
        return -1;
    EVP_MD_CTX *ctx = NULL;
    if (digest_begin(&ctx) != 0) return -2;
    size_t logical = 0;
    for (size_t i = 0; i < segment_count; ++i) {
        const one_g02_hash_segment *s = &segments[i];
        size_t start = (size_t)s->start;
        size_t len = (size_t)s->length;
        if (!len || logical > target_len || len > target_len - logical) {
            EVP_MD_CTX_free(ctx);
            return -3;
        }
        const uint8_t *p = NULL;
        if (s->kind == 0u) {
            if (start > source_len || len > source_len - start) {
                EVP_MD_CTX_free(ctx);
                return -4;
            }
            p = source + start;
        } else if (s->kind == 1u) {
            /* Surprise start is the logical target offset in the native plan. */
            if (start != logical || start > target_len || len > target_len - start) {
                EVP_MD_CTX_free(ctx);
                return -5;
            }
            p = target + start;
        } else {
            EVP_MD_CTX_free(ctx);
            return -6;
        }
        if (EVP_DigestUpdate(ctx, p, len) != 1) {
            EVP_MD_CTX_free(ctx);
            return -7;
        }
        logical += len;
    }
    if (logical != target_len) {
        EVP_MD_CTX_free(ctx);
        return -8;
    }
    return digest_end(ctx, out) == 0 ? 0 : -9;
}
