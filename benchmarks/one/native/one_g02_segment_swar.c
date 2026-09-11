#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind; /* 0=source Ref, 1=target Surprise */
} one_g02_segment;

typedef struct {
    uint64_t compared_target_bytes;
    uint64_t segments;
} one_g02_segment_stats;

static int is_ref_byte(const uint8_t *src, const uint8_t *dst, size_t i) {
    return i > 0 && dst[i] == src[i - 1];
}

static uint64_t load_u64(const uint8_t *p) {
    uint64_t v;
    memcpy(&v, p, sizeof(v));
    return v;
}

/* True iff at least one byte in x is zero. */
static int has_zero_byte(uint64_t x) {
    const uint64_t lo = UINT64_C(0x0101010101010101);
    const uint64_t hi = UINT64_C(0x8080808080808080);
    return ((x - lo) & ~x & hi) != 0;
}

/*
 * Prove that the next eight positions remain in the current Segment class.
 * For Ref, every xor byte must be zero. For Surprise, no xor byte may be zero.
 * This is a proof, not a predictor: mixed words fall back to scalar transitions.
 */
static int uniform8(const uint8_t *src, const uint8_t *dst, size_t i, int ref) {
    if (i == 0) return 0;
    const uint64_t a = load_u64(dst + i);
    const uint64_t b = load_u64(src + i - 1);
    const uint64_t x = a ^ b;
    return ref ? (x == 0) : !has_zero_byte(x);
}

int one_g02_segment_plan_swar(const uint8_t *src, const uint8_t *dst, size_t n,
                              one_g02_segment *out, size_t cap,
                              one_g02_segment_stats *stats) {
    if (!src || !dst || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    if (n == 0) return 0;

    size_t i = 0;
    while (i < n) {
        const int ref = is_ref_byte(src, dst, i);
        const size_t begin = i++;

        while (i < n) {
            /* Skip only words whose classification is proved uniform. */
            while (i + 8u <= n && uniform8(src, dst, i, ref))
                i += 8u;
            if (i >= n || is_ref_byte(src, dst, i) != ref)
                break;
            ++i;
        }

        const size_t len = i - begin;
        const size_t idx = (size_t)stats->segments++;
        if (!out || idx >= cap || begin > UINT32_MAX || len > UINT32_MAX)
            return -2;
        out[idx].kind = ref ? 0u : 1u;
        out[idx].start = (uint32_t)(ref ? begin - 1u : begin);
        out[idx].length = (uint32_t)len;
    }
    return 0;
}
