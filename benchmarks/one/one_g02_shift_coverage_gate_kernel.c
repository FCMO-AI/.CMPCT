#include <stddef.h>
#include <stdint.h>

/*
 * ONE-G0.2 writer-only shift coverage probe.
 *
 * Every 64 source bytes in the first half, compare one byte against the
 * corresponding second-half byte.  Only when zero shift fails do we inspect
 * the four bounded non-zero shifts.  This changes the observation topology
 * from eight fixed points to coverage proportional to relation length while
 * keeping worst-case modeled read traffic at 10/128 = 7.8125% of input.
 *
 * This is discovery research only: no reader opcode or stored representation.
 */
typedef struct {
    uint64_t samples;
    uint64_t zero_shift_matches;
    uint64_t compared_bytes;
    uint64_t exclusive_hits[4];
    uint64_t best_hits;
    int64_t best_shift;
} one_g02_shift_coverage_result;

int one_g02_shift_coverage_gate(const uint8_t *data, size_t n,
                                one_g02_shift_coverage_result *out) {
    if (!out) return -1;
    *out = (one_g02_shift_coverage_result){0};
    if (!data || n < 1024) return 0;

    const size_t half = n / 2;
    static const int shifts[4] = {-2, -1, 1, 2};

    /* Keep two bytes of edge margin so every non-zero candidate is in bounds. */
    for (size_t p = 2; p + 2 < half && half + p + 2 < n; p += 64) {
        const int64_t q0 = (int64_t)half + (int64_t)p;
        ++out->samples;
        out->compared_bytes += 2;
        if (data[p] == data[q0]) {
            ++out->zero_shift_matches;
            continue;
        }

        for (size_t i = 0; i < 4; ++i) {
            const int64_t q = q0 + shifts[i];
            if (q < 0 || (uint64_t)q >= n) continue;
            out->compared_bytes += 2;
            if (data[p] == data[q]) ++out->exclusive_hits[i];
        }
    }

    for (size_t i = 0; i < 4; ++i) {
        if (out->exclusive_hits[i] > out->best_hits) {
            out->best_hits = out->exclusive_hits[i];
            out->best_shift = shifts[i];
        }
    }
    return 0;
}
