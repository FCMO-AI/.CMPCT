#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>
#if defined(__SSE2__)
#include <emmintrin.h>
#endif

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind;
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

static inline int emit_segment(one_g02_segment *out, size_t cap, size_t *count,
                               int ref, size_t begin, size_t end) {
    if (end <= begin) return 0;
    if (!out || *count >= cap || begin > UINT32_MAX || end - begin > UINT32_MAX) return -2;
    one_g02_segment *seg = &out[*count];
    seg->kind = ref ? 0u : 1u;
    seg->start = (uint32_t)(ref ? begin - 1 : begin);
    seg->length = (uint32_t)(end - begin);
    *count += 1;
    return 0;
}

int one_g02_segment_scalar_exact_v2(const uint8_t *src, const uint8_t *dst, size_t n,
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

int one_g02_segment_sse2_transition_exact_v2(const uint8_t *src, const uint8_t *dst, size_t n,
                                             one_g02_segment *out, size_t cap,
                                             one_g02_segment_stats *stats) {
    if (!src || !dst || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    if (n == 0) return 0;
#if !defined(__SSE2__)
    return one_g02_segment_scalar_exact_v2(src, dst, n, out, cap, stats);
#else
    size_t count = 0;
    size_t run_begin = 0;
    int current_ref = 0;
    size_t i = 1;

    while (i + 16 <= n) {
        const __m128i a = _mm_loadu_si128((const __m128i *)(src + i - 1));
        const __m128i b = _mm_loadu_si128((const __m128i *)(dst + i));
        const uint32_t p = (uint32_t)_mm_movemask_epi8(_mm_cmpeq_epi8(a, b)) & 0xffffu;
        uint32_t transitions = p ^ (((p << 1) | (uint32_t)current_ref) & 0xffffu);

        if (transitions == 0u) {
            i += 16;
            continue;
        }

        if (transitions == 0xffffu) {
            /* Every position toggles: emit exact boundaries with no ctz/mask loop. */
            for (unsigned bit = 0; bit < 16u; ++bit) {
                const size_t boundary = i + bit;
                if (emit_segment(out, cap, &count, current_ref, run_begin, boundary) != 0) return -2;
                run_begin = boundary;
                current_ref ^= 1;
            }
            i += 16;
            continue;
        }

        while (transitions) {
            const unsigned bit = (unsigned)__builtin_ctz(transitions);
            const size_t boundary = i + bit;
            if (emit_segment(out, cap, &count, current_ref, run_begin, boundary) != 0) return -2;
            run_begin = boundary;
            current_ref ^= 1;
            transitions &= transitions - 1u;
        }
        current_ref = (int)((p >> 15) & 1u);
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

int one_g02_segment_sse2_transition_timed_pair_v2(
    const uint8_t *src, const uint8_t *dst, size_t n,
    one_g02_segment *scalar_out, one_g02_segment *candidate_out,
    size_t cap, size_t rounds, uint64_t *scalar_ns, uint64_t *candidate_ns
) {
    if (!src || !dst || !scalar_out || !candidate_out || !scalar_ns || !candidate_ns || rounds == 0) return -1;
    for (size_t r = 0; r < rounds; ++r) {
        const int candidate_first = (int)(r & 1u);
        for (int arm = 0; arm < 2; ++arm) {
            const int candidate = candidate_first ? (arm == 0) : (arm == 1);
            one_g02_segment_stats stats = {0,0};
            const uint64_t t0 = now_ns();
            const int rc = candidate
                ? one_g02_segment_sse2_transition_exact_v2(src, dst, n, candidate_out, cap, &stats)
                : one_g02_segment_scalar_exact_v2(src, dst, n, scalar_out, cap, &stats);
            const uint64_t elapsed = now_ns() - t0;
            if (rc != 0) return -2;
            if (candidate) candidate_ns[r] = elapsed;
            else scalar_ns[r] = elapsed;
        }
    }
    return 0;
}
