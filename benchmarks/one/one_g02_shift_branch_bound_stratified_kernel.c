#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * ONE-G0.2 writer-only branch-and-bound proof-topology rehabilitation.
 *
 * The original two-stage gate proved that cheap sparse coverage can nominate
 * useful signed-shift reuse at very low cost, but its exact proofs all came
 * from the relation front. A contiguous damaged prefix therefore erased every
 * proof while leaving most of the relation reusable.
 *
 * This superseding testbed keeps the frozen coverage semantics and exact-proof
 * budget, but distributes proof ownership across sixteen equal relation
 * strata. Each stratum may contribute at most one exact 64-byte proof, chosen
 * only from a cell whose coverage sample supports the nominated shift. The
 * reader-visible ONE algebra is unchanged; this is writer discovery only.
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
    uint64_t strata_with_support;
} one_g02_shift_branch_bound_stratified_result;

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

int one_g02_shift_branch_bound_stratified(const uint8_t *data, size_t n,
                                           one_g02_shift_branch_bound_stratified_result *out) {
    if (!out) return -1;
    *out = (one_g02_shift_branch_bound_stratified_result){0};
    if (!data || n < 1024) return 0;

    const size_t half = n / 2;
    static const int shifts[4] = {-2, -1, 1, 2};
    uint64_t hits[4] = {0, 0, 0, 0};

    /* Frozen stage-1 semantics from the successful branch-bound gate. */
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
    if (out->best_hits < 4 || out->best_hits * 2 < out->samples) return 0;

    const int64_t d = out->best_shift;
    const size_t cells = half / 64;
    if (cells == 0) return 0;

    /*
     * One coverage-supported proof owner per stratum. This removes the phase
     * concentration of the retired fixed-front topology without increasing
     * the sixteen-attempt ceiling. A stratum is allowed to fail; four exact
     * proofs across independent strata remain the admission requirement.
     */
    for (size_t s = 0; s < 16 && out->proof_attempts < 16; ++s) {
        size_t first_cell = (cells * s) / 16;
        size_t end_cell = (cells * (s + 1)) / 16;
        if (end_cell <= first_cell) continue;

        int found_support = 0;
        size_t proof_p = 0;
        for (size_t cell = first_cell; cell < end_cell; ++cell) {
            const size_t p0 = cell * 64;
            if (p0 + 64 > half) break;
            const size_t sample_p = p0 + 2;
            const int64_t q0 = (int64_t)half + (int64_t)sample_p;
            const int64_t q = q0 + d;
            if (sample_p + 2 >= half || q < 0 || (uint64_t)q >= n) continue;
            /* Match stage 1: zero-shift equality is not evidence for d. */
            if (data[sample_p] == data[q0]) continue;
            out->coverage_compared_bytes += 2;
            if (data[sample_p] == data[q]) {
                found_support = 1;
                proof_p = p0;
                break;
            }
        }
        if (!found_support) continue;
        ++out->strata_with_support;
        const int64_t proof_q = (int64_t)half + (int64_t)proof_p + d;
        if (proof_q < 0 || (uint64_t)proof_q + 64 > n) continue;
        ++out->proof_attempts;
        if (exact64_counted(data + proof_p, data + proof_q, &out->proof_compared_bytes)) {
            ++out->exact_proofs;
            if (out->exact_proofs >= 4) break;
        }
    }
    return 0;
}
