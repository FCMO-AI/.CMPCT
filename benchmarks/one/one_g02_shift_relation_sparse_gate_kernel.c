#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t samples, zero_shift_matches, coverage_compared_bytes, best_hits;
    int64_t best_shift;
    uint64_t proof_attempts, exact_proofs, proof_compared_bytes, strata_with_support;
} one_g02_sparse_gate_result;

typedef struct {
    double gated_ns_per_batch;
    double baseline_ns_per_batch;
    uint64_t gate_compared_bytes;
    uint64_t gate_fires;
    uint64_t gate_rejects;
    uint64_t baseline_enabled;
    uint64_t gated_enabled;
    uint64_t productive_retained;
    uint64_t false_controls;
} one_g02_sparse_gate_measurement;

extern int one_g02_shift_relation_safe_dispatch(
    const uint8_t *, const uint8_t *, size_t, one_g02_sparse_gate_result *);

static uint64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}

/*
 * Cheap, content-only falsifier for an already nominated relation pair.
 *
 * Sixteen evenly spaced probes test exactly the four bounded shifts already owned
 * by the downstream proof kernel. Two supporting probes are sufficient to pass.
 * That threshold is intentionally permissive: under independent uniform bytes the
 * expected support for one shift is only 16/256, while a real broad shifted relation
 * should support many strata. The exact downstream proof remains authoritative.
 *
 * Returns 1 when full proof was executed, 0 when the pair was cheaply rejected,
 * and a negative value on invalid input. `compared_bytes` charges every byte read by
 * the gate (two bytes per comparison), including zero-shift falsification.
 */
int one_g02_shift_relation_sparse_gate(
    const uint8_t *src, const uint8_t *dst, size_t relation_len,
    one_g02_sparse_gate_result *out, uint64_t *compared_bytes)
{
    if (!out || !compared_bytes) return -1;
    *out = (one_g02_sparse_gate_result){0};
    *compared_bytes = 0;
    if (!src || !dst || relation_len < 1024) return 0;

    static const int shifts[4] = {-2, -1, 1, 2};
    uint32_t hits[4] = {0, 0, 0, 0};
    for (size_t s = 0; s < 16; ++s) {
        size_t p = ((s + 1) * relation_len) / 17;
        if (p < 2) p = 2;
        if (p + 2 >= relation_len) p = relation_len - 3;
        *compared_bytes += 2;
        if (src[p] == dst[p]) continue;
        for (size_t i = 0; i < 4; ++i) {
            const int64_t q = (int64_t)p + shifts[i];
            if (q < 0 || (uint64_t)q >= relation_len) continue;
            *compared_bytes += 2;
            if (src[p] == dst[q]) ++hits[i];
        }
    }

    uint32_t best = 0;
    for (size_t i = 0; i < 4; ++i) if (hits[i] > best) best = hits[i];
    if (best < 2) return 0;
    return one_g02_shift_relation_safe_dispatch(src, dst, relation_len, out) < 0 ? -2 : 1;
}

static int enabled(const one_g02_sparse_gate_result *r) {
    return r->exact_proofs >= 4;
}

/*
 * Measure a mixed batch encoded as [src0|dst0|src1|dst1|...]. Both arms see the
 * same pair order and relation bytes. Timing is A-B-B-A so fixed frequency drift is
 * less likely to masquerade as a gate win. Pair enumeration is explicit and charged
 * only as loop/control work here; discovery of arbitrary pair identities remains out
 * of scope and must be paid by the later fused observer experiment.
 */
int one_g02_shift_relation_sparse_gate_measure(
    const uint8_t *packed, size_t relation_len, size_t pair_count, size_t batch,
    one_g02_sparse_gate_measurement *m)
{
    if (!packed || !m || relation_len < 1024 || !pair_count || !batch) return -1;
    one_g02_sparse_gate_result r = {0};
    uint64_t reads = 0, t, a1, a2, b1, b2;

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
            if (one_g02_shift_relation_sparse_gate(src, dst, relation_len, &r, &reads) < 0) return -3;
        }
    b1 = now_ns() - t;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k)
        for (size_t i = 0; i < pair_count; ++i) {
            const uint8_t *src = packed + (i * 2) * relation_len;
            const uint8_t *dst = src + relation_len;
            if (one_g02_shift_relation_sparse_gate(src, dst, relation_len, &r, &reads) < 0) return -4;
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

    *m = (one_g02_sparse_gate_measurement){0};
    m->baseline_ns_per_batch = ((double)a1 + (double)a2) / (2.0 * (double)batch);
    m->gated_ns_per_batch = ((double)b1 + (double)b2) / (2.0 * (double)batch);

    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2) * relation_len;
        const uint8_t *dst = src + relation_len;
        one_g02_sparse_gate_result base = {0}, gate = {0};
        uint64_t gate_reads = 0;
        if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &base) < 0) return -6;
        int fired = one_g02_shift_relation_sparse_gate(src, dst, relation_len, &gate, &gate_reads);
        if (fired < 0) return -7;
        m->gate_compared_bytes += gate_reads;
        m->gate_fires += fired ? 1 : 0;
        m->gate_rejects += fired ? 0 : 1;
        m->baseline_enabled += enabled(&base) ? 1 : 0;
        m->gated_enabled += enabled(&gate) ? 1 : 0;
        m->productive_retained += enabled(&base) && enabled(&gate) && base.best_shift == gate.best_shift;
        m->false_controls += fired && !enabled(&gate);
    }
    return 0;
}
