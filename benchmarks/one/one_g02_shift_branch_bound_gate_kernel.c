#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * ONE-G0.2 writer-only branch-and-bound shift testbed.
 *
 * Stage 1: cheap one-byte coverage over the half-to-half causal test relation.
 * Stage 2: only after one signed displacement owns a majority, require exact
 * 64-byte proofs.  This tests whether cheap resemblance can nominate expensive
 * exact discovery without confusing resemblance with reconstructable reuse.
 *
 * This is not a general product dispatch and not reader-visible ONE syntax.
 */
typedef struct {
    uint64_t samples;
    uint64_t zero_shift_matches;
    uint64_t coverage_compared_bytes;
    uint64_t best_hits;
    int64_t best_shift;
    uint64_t proof_attempts;
    uint64_t exact_proofs;
    uint64_t proof_compared_bytes;
} one_g02_shift_branch_bound_result;

static int exact64_counted(const uint8_t *a, const uint8_t *b, uint64_t *bytes) {
    for (size_t i = 0; i < 64; i += 8) {
        uint64_t x, y;
        memcpy(&x, a + i, 8);
        memcpy(&y, b + i, 8);
        *bytes += 16;
        if (x != y) return 0;
    }
    return 1;
}

int one_g02_shift_branch_bound_gate(const uint8_t *data, size_t n,
                                    one_g02_shift_branch_bound_result *out) {
    if (!out) return -1;
    *out = (one_g02_shift_branch_bound_result){0};
    if (!data || n < 1024) return 0;

    const size_t half = n / 2;
    static const int shifts[4] = {-2, -1, 1, 2};
    uint64_t hits[4] = {0, 0, 0, 0};

    for (size_t p = 2; p + 2 < half && half + p + 2 < n; p += 64) {
        const int64_t q0 = (int64_t)half + (int64_t)p;
        ++out->samples;
        out->coverage_compared_bytes += 2;
        if (data[p] == data[q0]) {
            ++out->zero_shift_matches;
            continue;
        }
        for (size_t i = 0; i < 4; ++i) {
            const int64_t q = q0 + shifts[i];
            if (q < 0 || (uint64_t)q >= n) continue;
            out->coverage_compared_bytes += 2;
            if (data[p] == data[q]) ++hits[i];
        }
    }

    for (size_t i = 0; i < 4; ++i) {
        if (hits[i] > out->best_hits) {
            out->best_hits = hits[i];
            out->best_shift = shifts[i];
        }
    }

    /* Stage 2 is unreachable unless coverage has both the inherited four-hit
     * floor and strict majority support. */
    if (out->best_hits < 4 || out->best_hits * 2 < out->samples) return 0;

    const int64_t d = out->best_shift;
    /* Search sequential 64-byte cells. Stop once four exact proofs exist or
     * sixteen candidates have been tested. Unlike fixed eight point samples,
     * the proof sites are not the same sparse sites that nominated the shift. */
    for (size_t p = 0; p + 64 <= half && out->proof_attempts < 16; p += 64) {
        const int64_t q = (int64_t)half + (int64_t)p + d;
        if (q < 0 || (uint64_t)q + 64 > n) continue;
        ++out->proof_attempts;
        if (exact64_counted(data + p, data + q, &out->proof_compared_bytes)) {
            ++out->exact_proofs;
            if (out->exact_proofs >= 4) break;
        }
    }
    return 0;
}
