#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#if defined(__SSE2__)
#include <emmintrin.h>
#endif

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind; /* 0=source Ref, 1=target Surprise */
} one_g02_segment;

typedef struct {
    uint64_t compared_target_bytes;
    uint64_t segments;
} one_g02_segment_stats;

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int emit_segment(one_g02_segment *out, size_t cap, size_t *count,
                        int ref, size_t begin, size_t end) {
    if (end <= begin) return 0;
    if (!out || *count >= cap || begin > UINT32_MAX || end - begin > UINT32_MAX) return -2;
    out[*count].kind = ref ? 0u : 1u;
    out[*count].start = (uint32_t)(ref ? begin - 1 : begin);
    out[*count].length = (uint32_t)(end - begin);
    *count += 1;
    return 0;
}

int one_g02_segment_scalar_exact(const uint8_t *src, const uint8_t *dst, size_t n,
                                 one_g02_segment *out, size_t cap,
                                 one_g02_segment_stats *stats) {
    if (!src || !dst || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    if (n == 0) return 0;
    size_t count = 0;
    size_t i = 0;
    while (i < n) {
        const int ref = i > 0 && dst[i] == src[i - 1];
        const size_t begin = i++;
        while (i < n && (i > 0 && dst[i] == src[i - 1]) == ref) ++i;
        if (emit_segment(out, cap, &count, ref, begin, i) != 0) return -2;
    }
    stats->segments = count;
    return 0;
}

int one_g02_segment_sse2_exact(const uint8_t *src, const uint8_t *dst, size_t n,
                               one_g02_segment *out, size_t cap,
                               one_g02_segment_stats *stats) {
    if (!src || !dst || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    if (n == 0) return 0;
#if !defined(__SSE2__)
    return one_g02_segment_scalar_exact(src, dst, n, out, cap, stats);
#else
    size_t count = 0;
    size_t run_begin = 0;
    int current_ref = 0; /* i=0 is always Surprise. */
    size_t i = 1;

    while (i + 16 <= n) {
        const __m128i a = _mm_loadu_si128((const __m128i *)(src + i - 1));
        const __m128i b = _mm_loadu_si128((const __m128i *)(dst + i));
        const __m128i eq = _mm_cmpeq_epi8(a, b);
        const uint32_t mask = (uint32_t)_mm_movemask_epi8(eq) & 0xffffu;
        unsigned consumed = 0;
        while (consumed < 16u) {
            const unsigned remaining = 16u - consumed;
            const uint32_t rem_mask = (1u << remaining) - 1u;
            const uint32_t tail = (mask >> consumed) & rem_mask;
            const int ref = (int)(tail & 1u);
            const uint32_t diff = ref ? ((~tail) & rem_mask) : (tail & rem_mask);
            const unsigned run = diff ? (unsigned)__builtin_ctz(diff) : remaining;
            const size_t sub_begin = i + consumed;
            if (ref != current_ref) {
                if (emit_segment(out, cap, &count, current_ref, run_begin, sub_begin) != 0) return -2;
                run_begin = sub_begin;
                current_ref = ref;
            }
            consumed += run;
        }
        i += 16;
    }

    while (i < n) {
        const int ref = dst[i] == src[i - 1];
        if (ref != current_ref) {
            if (emit_segment(out, cap, &count, current_ref, run_begin, i) != 0) return -2;
            run_begin = i;
            current_ref = ref;
        }
        ++i;
    }
    if (emit_segment(out, cap, &count, current_ref, run_begin, n) != 0) return -2;
    stats->segments = count;
    return 0;
#endif
}

int one_g02_segment_sse2_timed_pair(const uint8_t *src, const uint8_t *dst, size_t n,
                                    one_g02_segment *scalar_out, one_g02_segment *sse2_out,
                                    size_t cap, size_t rounds,
                                    uint64_t *scalar_ns, uint64_t *sse2_ns) {
    if (!src || !dst || !scalar_out || !sse2_out || !scalar_ns || !sse2_ns || rounds == 0) return -1;
    for (size_t r = 0; r < rounds; ++r) {
        const int candidate_first = (int)(r & 1u);
        for (int arm = 0; arm < 2; ++arm) {
            const int candidate = candidate_first ? (arm == 0) : (arm == 1);
            one_g02_segment_stats stats = {0, 0};
            const uint64_t t0 = now_ns();
            const int rc = candidate
                ? one_g02_segment_sse2_exact(src, dst, n, sse2_out, cap, &stats)
                : one_g02_segment_scalar_exact(src, dst, n, scalar_out, cap, &stats);
            const uint64_t elapsed = now_ns() - t0;
            if (rc != 0) return -2;
            if (candidate) sse2_ns[r] = elapsed;
            else scalar_ns[r] = elapsed;
        }
    }
    return 0;
}
