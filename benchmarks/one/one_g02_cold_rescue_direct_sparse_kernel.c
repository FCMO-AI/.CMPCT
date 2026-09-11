#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t samples, zero_shift_matches, coverage_compared_bytes, best_hits;
    int64_t best_shift;
    uint64_t proof_attempts, exact_proofs, proof_compared_bytes, strata_with_support;
} one_g02_relation_result;

typedef struct {
    double eager_ns_per_batch;
    double sparse_ns_per_batch;
    uint64_t sparse_gate_compared_bytes;
    uint64_t sparse_gate_fires;
    uint64_t sparse_gate_rejects;
    uint64_t eager_exact_pairs;
    uint64_t sparse_exact_executions;
    uint64_t exact_positive_pairs;
    uint64_t productive_retained;
    uint64_t negative_enabled;
} one_g02_direct_sparse_measurement;

extern int one_g02_shift_relation_safe_dispatch(
    const uint8_t *, const uint8_t *, size_t, one_g02_relation_result *);
extern int one_g02_shift_relation_sparse_gate(
    const uint8_t *, const uint8_t *, size_t,
    one_g02_relation_result *, uint64_t *);

static uint64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}

static int enabled(const one_g02_relation_result *r) { return r->exact_proofs >= 4; }

static int eager_batch(const uint8_t *packed, size_t relation_len, size_t pair_count) {
    int checksum = 0;
    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2u) * relation_len;
        const uint8_t *dst = src + relation_len;
        one_g02_relation_result r = {0};
        if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &r) < 0) return -1;
        checksum += enabled(&r) ? (int)(r.best_shift + 7) : 1;
    }
    return checksum;
}

static int sparse_batch(const uint8_t *packed, size_t relation_len, size_t pair_count) {
    int checksum = 0;
    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2u) * relation_len;
        const uint8_t *dst = src + relation_len;
        one_g02_relation_result r = {0};
        uint64_t compared = 0;
        int fired = one_g02_shift_relation_sparse_gate(src, dst, relation_len, &r, &compared);
        if (fired < 0) return -1;
        checksum += enabled(&r) ? (int)(r.best_shift + 7) : 1;
    }
    return checksum;
}

int one_g02_direct_sparse_measure(const uint8_t *packed, size_t relation_len,
                                  size_t pair_count, size_t batch,
                                  one_g02_direct_sparse_measurement *m) {
    if (!packed || !m || relation_len < 1024 || !pair_count || !batch) return -1;
    uint64_t t, a1, a2, b1, b2;
    volatile int escape = 0;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x=eager_batch(packed,relation_len,pair_count); if(x<0)return -2; escape^=x; }
    a1 = now_ns() - t;
    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x=sparse_batch(packed,relation_len,pair_count); if(x<0)return -3; escape^=x; }
    b1 = now_ns() - t;
    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x=sparse_batch(packed,relation_len,pair_count); if(x<0)return -4; escape^=x; }
    b2 = now_ns() - t;
    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x=eager_batch(packed,relation_len,pair_count); if(x<0)return -5; escape^=x; }
    a2 = now_ns() - t;
    (void)escape;

    *m = (one_g02_direct_sparse_measurement){0};
    m->eager_ns_per_batch = ((double)a1 + (double)a2) / (2.0 * (double)batch);
    m->sparse_ns_per_batch = ((double)b1 + (double)b2) / (2.0 * (double)batch);
    m->eager_exact_pairs = pair_count;

    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2u) * relation_len;
        const uint8_t *dst = src + relation_len;
        one_g02_relation_result eager = {0}, sparse = {0};
        uint64_t compared = 0;
        if (one_g02_shift_relation_safe_dispatch(src,dst,relation_len,&eager) < 0) return -6;
        int eager_on = enabled(&eager);
        m->exact_positive_pairs += eager_on ? 1u : 0u;
        int fired = one_g02_shift_relation_sparse_gate(src,dst,relation_len,&sparse,&compared);
        if (fired < 0) return -7;
        m->sparse_gate_compared_bytes += compared;
        m->sparse_gate_fires += fired ? 1u : 0u;
        m->sparse_gate_rejects += fired ? 0u : 1u;
        m->sparse_exact_executions += fired ? 1u : 0u;
        int sparse_on = enabled(&sparse);
        if (eager_on && sparse_on && eager.best_shift == sparse.best_shift) ++m->productive_retained;
        if (!eager_on && sparse_on) ++m->negative_enabled;
    }
    return 0;
}
