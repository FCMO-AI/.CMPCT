#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * ONE-G0.2 writer-only proof-led branch-and-bound admission.
 *
 * Supersedes, but does not mutate, the stratified gate after the frozen
 * contiguous-damage envelope showed that its global majority prerequisite
 * blocks exact proof while 16-32 KiB of useful shifted relation survives.
 *
 * This testbed keeps the inherited 64-byte coverage stride, signed shift set,
 * four-hit nomination floor, sixteen deterministic relation strata, 64-byte
 * exact proof, four-proof admission threshold and sixteen-attempt ceiling.
 * The only causal change is removal of the global >=50% coverage-majority
 * prerequisite. Specificity must now be earned by distributed exact proofs.
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
} one_g02_shift_branch_bound_proof_led_result;

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

int one_g02_shift_branch_bound_proof_led(const uint8_t *data, size_t n,
                                          one_g02_shift_branch_bound_proof_led_result *out) {
    if (!out) return -1;
    *out = (one_g02_shift_branch_bound_proof_led_result){0};
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

    /* Frozen inherited minimum support. Exact proof owns specificity now. */
    if (out->best_hits < 4) return 0;

    const int64_t d = out->best_shift;
    const size_t cells = half / 64;
    if (cells == 0) return 0;

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
