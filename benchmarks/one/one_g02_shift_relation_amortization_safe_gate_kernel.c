#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t samples, zero_shift_matches, coverage_compared_bytes, best_hits;
    int64_t best_shift;
    uint64_t proof_attempts, exact_proofs, proof_compared_bytes, strata_with_support;
} one_g02_gate_result;

typedef struct {
    double candidate_ns_per_batch;
    double baseline_ns_per_batch;
    uint64_t gate_compared_bytes;
    uint64_t gate_fires;
    uint64_t gate_rejects;
    uint64_t direct_pairs;
    uint64_t baseline_enabled;
    uint64_t candidate_enabled;
    uint64_t productive_retained;
    uint64_t false_controls;
} one_g02_amort_measurement;

extern int one_g02_shift_relation_safe_dispatch(
    const uint8_t *, const uint8_t *, size_t, one_g02_gate_result *);
extern int one_g02_shift_relation_sparse_gate(
    const uint8_t *, const uint8_t *, size_t, one_g02_gate_result *, uint64_t *);

static uint64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}

static int enabled(const one_g02_gate_result *r) { return r->exact_proofs >= 4; }

/* 160 bytes is the already-frozen maximum probe cost per relation pair.
 * 1% is the already-frozen read budget, so the exact amortization boundary is
 * 160 / 0.01 = 16000 bytes.  This function changes no detector semantics. */
int one_g02_shift_relation_amortization_safe_gate(
    const uint8_t *src, const uint8_t *dst, size_t relation_len,
    one_g02_gate_result *out, uint64_t *compared_bytes, int *used_gate)
{
    if (!out || !compared_bytes || !used_gate) return -1;
    *compared_bytes = 0;
    *used_gate = 0;
    if (relation_len < 16000u) {
        return one_g02_shift_relation_safe_dispatch(src, dst, relation_len, out) < 0 ? -2 : 1;
    }
    *used_gate = 1;
    return one_g02_shift_relation_sparse_gate(src, dst, relation_len, out, compared_bytes);
}

int one_g02_shift_relation_amortization_safe_measure(
    const uint8_t *packed, size_t relation_len, size_t pair_count, size_t batch,
    one_g02_amort_measurement *m)
{
    if (!packed || !m || relation_len < 1024 || !pair_count || !batch) return -1;
    one_g02_gate_result r = {0};
    uint64_t reads = 0, t, a1, a2, b1, b2;
    int used = 0;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k)
        for (size_t i = 0; i < pair_count; ++i) {
            const uint8_t *src = packed + (i * 2) * relation_len;
            const uint8_t *dst = src + relation_len;
            if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &r) < 0) return -2;
        }
    a1 = now_ns() - t;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k)
        for (size_t i = 0; i < pair_count; ++i) {
            const uint8_t *src = packed + (i * 2) * relation_len;
            const uint8_t *dst = src + relation_len;
            if (one_g02_shift_relation_amortization_safe_gate(src, dst, relation_len, &r, &reads, &used) < 0) return -3;
        }
    b1 = now_ns() - t;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k)
        for (size_t i = 0; i < pair_count; ++i) {
            const uint8_t *src = packed + (i * 2) * relation_len;
            const uint8_t *dst = src + relation_len;
            if (one_g02_shift_relation_amortization_safe_gate(src, dst, relation_len, &r, &reads, &used) < 0) return -4;
        }
    b2 = now_ns() - t;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k)
        for (size_t i = 0; i < pair_count; ++i) {
            const uint8_t *src = packed + (i * 2) * relation_len;
            const uint8_t *dst = src + relation_len;
            if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &r) < 0) return -5;
        }
    a2 = now_ns() - t;

    *m = (one_g02_amort_measurement){0};
    m->baseline_ns_per_batch = ((double)a1 + (double)a2) / (2.0 * (double)batch);
    m->candidate_ns_per_batch = ((double)b1 + (double)b2) / (2.0 * (double)batch);

    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2) * relation_len;
        const uint8_t *dst = src + relation_len;
        one_g02_gate_result base = {0}, cand = {0};
        uint64_t gate_reads = 0;
        int used_gate = 0;
        if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &base) < 0) return -6;
        int fired = one_g02_shift_relation_amortization_safe_gate(
            src, dst, relation_len, &cand, &gate_reads, &used_gate);
        if (fired < 0) return -7;
        m->gate_compared_bytes += gate_reads;
        m->direct_pairs += used_gate ? 0 : 1;
        if (used_gate) {
            m->gate_fires += fired ? 1 : 0;
            m->gate_rejects += fired ? 0 : 1;
            m->false_controls += fired && !enabled(&cand);
        }
        m->baseline_enabled += enabled(&base) ? 1 : 0;
        m->candidate_enabled += enabled(&cand) ? 1 : 0;
        m->productive_retained += enabled(&base) && enabled(&cand) && base.best_shift == cand.best_shift;
    }
    return 0;
}
