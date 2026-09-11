#include <stddef.h>
#include <stdint.h>

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

static int emit_plan(const uint8_t *src, const uint8_t *dst, size_t n,
                     one_g02_segment *out, size_t cap,
                     one_g02_segment_stats *stats, int count_only) {
    if (!src || !dst || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    if (n == 0) return 0;
    size_t i = 0;
    while (i < n) {
        const int ref = is_ref_byte(src, dst, i);
        const size_t begin = i++;
        while (i < n && is_ref_byte(src, dst, i) == ref) ++i;
        const size_t len = i - begin;
        const size_t idx = (size_t)stats->segments++;
        if (!count_only) {
            if (!out || idx >= cap || begin > UINT32_MAX || len > UINT32_MAX) return -2;
            out[idx].kind = ref ? 0u : 1u;
            out[idx].start = (uint32_t)(ref ? begin - 1 : begin);
            out[idx].length = (uint32_t)len;
        }
    }
    return 0;
}

int one_g02_segment_plan_one_pass(const uint8_t *src, const uint8_t *dst, size_t n,
                                  one_g02_segment *out, size_t cap,
                                  one_g02_segment_stats *stats) {
    return emit_plan(src, dst, n, out, cap, stats, 0);
}

int one_g02_segment_plan_two_pass(const uint8_t *src, const uint8_t *dst, size_t n,
                                  one_g02_segment *out, size_t cap,
                                  one_g02_segment_stats *stats) {
    one_g02_segment_stats first = {0,0}, second = {0,0};
    if (emit_plan(src, dst, n, NULL, 0, &first, 1) != 0) return -1;
    if (first.segments > cap) return -2;
    if (emit_plan(src, dst, n, out, cap, &second, 0) != 0) return -3;
    if (first.segments != second.segments) return -4;
    stats->compared_target_bytes = first.compared_target_bytes + second.compared_target_bytes;
    stats->segments = second.segments;
    return 0;
}
