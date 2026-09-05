#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * ONE-G0.2 structural-transfer testbed for proof-led relation admission.
 *
 * Unlike the earlier half-to-half instruments, this kernel receives arbitrary
 * source/target region offsets and a relation length. It keeps the promoted
 * proof-led semantics: 64-byte coverage stride, shifts {-2,-1,+1,+2}, minimum
 * four support hits, sixteen deterministic strata, four exact 64-byte proofs,
 * maximum sixteen attempts. No reader-visible ONE operation is added.
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
} one_g02_shift_relation_result;

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

int one_g02_shift_branch_bound_relation(
    const uint8_t *data, size_t n,
    size_t source_offset, size_t target_offset, size_t relation_len,
    one_g02_shift_relation_result *out
) {
    if (!out) return -1;
    *out = (one_g02_shift_relation_result){0};
    if (!data || relation_len < 1024) return 0;
    if (source_offset > n || target_offset > n) return -2;
    if (relation_len > n - source_offset || relation_len > n - target_offset) return -2;

    static const int shifts[4] = {-2, -1, 1, 2};
    uint64_t hits[4] = {0, 0, 0, 0};

    for (size_t p = 2; p + 2 < relation_len; p += 64) {
        const size_t a = source_offset + p;
        const size_t b0 = target_offset + p;
        ++out->samples;
        out->coverage_compared_bytes += 2;
        if (data[a] == data[b0]) {
            ++out->zero_shift_matches;
            continue;
        }
        for (size_t i = 0; i < 4; ++i) {
            const int64_t qb = (int64_t)b0 + shifts[i];
            if (qb < (int64_t)target_offset || qb < 0 || (uint64_t)qb >= n) continue;
            if ((uint64_t)qb >= target_offset + relation_len) continue;
            out->coverage_compared_bytes += 2;
            if (data[a] == data[qb]) ++hits[i];
        }
    }

    for (size_t i = 0; i < 4; ++i) {
        if (hits[i] > out->best_hits) {
            out->best_hits = hits[i];
            out->best_shift = shifts[i];
        }
    }
    if (out->best_hits < 4) return 0;

    const int64_t d = out->best_shift;
    const size_t cells = relation_len / 64;
    for (size_t s = 0; s < 16 && out->proof_attempts < 16; ++s) {
        size_t first_cell = (cells * s) / 16;
        size_t end_cell = (cells * (s + 1)) / 16;
        if (end_cell <= first_cell) continue;

        int found_support = 0;
        size_t proof_p = 0;
        for (size_t cell = first_cell; cell < end_cell; ++cell) {
            const size_t p0 = cell * 64;
            if (p0 + 64 > relation_len) break;
            const size_t sample_p = p0 + 2;
            if (sample_p + 2 >= relation_len) continue;
            const size_t a = source_offset + sample_p;
            const size_t b0 = target_offset + sample_p;
            const int64_t qb = (int64_t)b0 + d;
            if (qb < (int64_t)target_offset || qb < 0 || (uint64_t)qb >= n) continue;
            if ((uint64_t)qb >= target_offset + relation_len) continue;
            if (data[a] == data[b0]) continue;
            out->coverage_compared_bytes += 2;
            if (data[a] == data[qb]) {
                found_support = 1;
                proof_p = p0;
                break;
            }
        }
        if (!found_support) continue;
        ++out->strata_with_support;

        const size_t a0 = source_offset + proof_p;
        const int64_t qb0 = (int64_t)target_offset + (int64_t)proof_p + d;
        if (qb0 < (int64_t)target_offset || qb0 < 0) continue;
        if ((uint64_t)qb0 + 64 > target_offset + relation_len || (uint64_t)qb0 + 64 > n) continue;
        ++out->proof_attempts;
        if (exact64_counted(data + a0, data + qb0, &out->proof_compared_bytes)) {
            ++out->exact_proofs;
            if (out->exact_proofs >= 4) break;
        }
    }
    return 0;
}
