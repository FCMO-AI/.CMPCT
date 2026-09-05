#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * ONE-G0.2 writer-only opportunity falsifier.
 *
 * This is not a Law, reader opcode, or product representation.  It asks whether
 * small non-zero displacement can be established from samples that are *not*
 * already explained by zero-shift equality.  A zero-shift match therefore ends
 * that sample immediately: a non-zero match on the same sample would add no
 * exclusive shift evidence and need not be read.
 *
 * The equality primitive compares eight-byte words with early exit.  memcpy is
 * used to keep unaligned reads defined while allowing -O3 compilers to lower
 * them to efficient scalar/vector loads.  compared_bytes records the actual
 * modeled bytes loaded from both sides of each comparison (16 bytes/word).
 */
typedef struct {
    uint64_t samples;
    uint64_t zero_shift_matches;
    uint64_t exclusive_shift_matches;
    uint64_t compared_bytes;
    int64_t best_shift;
} one_g02_exclusive_shift_gate_result;

static int equal64_counted(const uint8_t *a, const uint8_t *b, uint64_t *compared_bytes) {
    for (size_t i = 0; i < 64; i += 8) {
        uint64_t x, y;
        memcpy(&x, a + i, sizeof(x));
        memcpy(&y, b + i, sizeof(y));
        *compared_bytes += 16;
        if (x != y) return 0;
    }
    return 1;
}

int one_g02_exclusive_shift_gate(const uint8_t *data, size_t n,
                                 one_g02_exclusive_shift_gate_result *out) {
    if (!out) return -1;
    *out = (one_g02_exclusive_shift_gate_result){0};
    if (!data || n < 1024) return 0;

    const size_t half = n / 2;
    if (half < 256 || n - half < 256) return 0;

    uint64_t exclusive_hits[4] = {0, 0, 0, 0};
    static const int shifts[4] = {-2, -1, 1, 2};

    for (size_t s = 0; s < 8; ++s) {
        const size_t p = 96 + ((half - 192 - 64) * (s + 1)) / 9;
        if (p + 64 > half) continue;
        ++out->samples;

        const uint8_t *a = data + p;
        const int64_t q0 = (int64_t)half + (int64_t)p;
        if (q0 < 0 || (uint64_t)q0 + 64 > n) continue;

        /* If zero shift already explains the sample, no non-zero comparison can
         * produce exclusive shift evidence for this sample. */
        if (equal64_counted(a, data + q0, &out->compared_bytes)) {
            ++out->zero_shift_matches;
            continue;
        }

        for (size_t i = 0; i < 4; ++i) {
            const int d = shifts[i];
            const int64_t q = q0 + d;
            if (q < 0 || (uint64_t)q + 64 > n) continue;
            if (equal64_counted(a, data + q, &out->compared_bytes)) {
                ++exclusive_hits[i];
            }
        }
    }

    uint64_t best = 0;
    int best_shift = 0;
    for (size_t i = 0; i < 4; ++i) {
        if (exclusive_hits[i] > best) {
            best = exclusive_hits[i];
            best_shift = shifts[i];
        }
    }
    out->exclusive_shift_matches = best;
    out->best_shift = best_shift;
    return 0;
}
