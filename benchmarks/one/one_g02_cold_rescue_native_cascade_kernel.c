#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define ONE_PHASES 5u
#define ONE_PER_PHASE 4u
#define ONE_WITNESSES 20u
#define ONE_STRIDE 32u
#define ONE_WORD 8u

static const uint32_t ONE_SOURCE_PHASES[ONE_PHASES] = {0u, 1u, 2u, 30u, 31u};

typedef struct {
    uint64_t samples, zero_shift_matches, coverage_compared_bytes, best_hits;
    int64_t best_shift;
    uint64_t proof_attempts, exact_proofs, proof_compared_bytes, strata_with_support;
} one_g02_relation_result;

typedef struct {
    uint64_t hash;
    uint32_t pos;
} one_phase_witness;

typedef struct {
    double eager_ns_per_batch;
    double gated_ns_per_batch;
    uint64_t phase_source_words;
    uint64_t phase_target_words;
    uint64_t phase_exact_word_compares;
    uint64_t phase_nominations;
    uint64_t sparse_gate_compared_bytes;
    uint64_t sparse_gate_fires;
    uint64_t sparse_gate_rejects;
    uint64_t eager_exact_pairs;
    uint64_t gated_exact_executions;
    uint64_t exact_positive_pairs;
    uint64_t productive_retained;
    uint64_t negative_enabled;
} one_g02_cold_rescue_measurement;

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

static uint64_t load_le64(const uint8_t *p) {
    return ((uint64_t)p[0]) | ((uint64_t)p[1] << 8) |
           ((uint64_t)p[2] << 16) | ((uint64_t)p[3] << 24) |
           ((uint64_t)p[4] << 32) | ((uint64_t)p[5] << 40) |
           ((uint64_t)p[6] << 48) | ((uint64_t)p[7] << 56);
}

static uint64_t mix64(uint64_t x) {
    x ^= x >> 30;
    x *= UINT64_C(0xBF58476D1CE4E5B9);
    x ^= x >> 27;
    x *= UINT64_C(0x94D049BB133111EB);
    x ^= x >> 31;
    return x;
}

static uint64_t word_hash(const uint8_t *p) {
    return mix64(load_le64(p) ^ UINT64_C(0x9E3779B97F4A7C15));
}

/* Max-heap by hash. Equal hashes deliberately do not replace an existing witness,
 * matching the frozen Python bottom-K semantics. */
static void heap_swap(one_phase_witness *a, one_phase_witness *b) {
    one_phase_witness t = *a; *a = *b; *b = t;
}

static void heap_offer(one_phase_witness heap[ONE_PER_PHASE], uint32_t *count,
                       uint64_t hash, uint32_t pos) {
    if (*count < ONE_PER_PHASE) {
        uint32_t i = (*count)++;
        heap[i].hash = hash; heap[i].pos = pos;
        while (i) {
            uint32_t parent = (i - 1u) >> 1;
            if (heap[parent].hash >= heap[i].hash) break;
            heap_swap(&heap[parent], &heap[i]);
            i = parent;
        }
        return;
    }
    if (hash >= heap[0].hash) return;
    heap[0].hash = hash; heap[0].pos = pos;
    uint32_t i = 0;
    for (;;) {
        uint32_t left = i * 2u + 1u;
        if (left >= ONE_PER_PHASE) break;
        uint32_t right = left + 1u;
        uint32_t worst = left;
        if (right < ONE_PER_PHASE && heap[right].hash > heap[left].hash) worst = right;
        if (heap[i].hash >= heap[worst].hash) break;
        heap_swap(&heap[i], &heap[worst]);
        i = worst;
    }
}

static uint32_t build_witnesses(const uint8_t *src, size_t n,
                                one_phase_witness out[ONE_WITNESSES],
                                uint64_t *sampled_words) {
    uint32_t out_count = 0;
    if (!src || n < ONE_WORD) return 0;
    for (uint32_t phase_i = 0; phase_i < ONE_PHASES; ++phase_i) {
        one_phase_witness heap[ONE_PER_PHASE] = {{0}};
        uint32_t count = 0;
        uint32_t phase = ONE_SOURCE_PHASES[phase_i];
        for (size_t pos = phase; pos + ONE_WORD <= n; pos += ONE_STRIDE) {
            uint64_t h = word_hash(src + pos);
            ++*sampled_words;
            heap_offer(heap, &count, h, (uint32_t)pos);
        }
        for (uint32_t j = 0; j < count; ++j) out[out_count++] = heap[j];
    }
    return out_count;
}

static void sort_witnesses(one_phase_witness *w, uint32_t n) {
    for (uint32_t i = 1; i < n; ++i) {
        one_phase_witness x = w[i];
        uint32_t j = i;
        while (j && (w[j-1].hash > x.hash ||
                     (w[j-1].hash == x.hash && w[j-1].pos > x.pos))) {
            w[j] = w[j-1]; --j;
        }
        w[j] = x;
    }
}

int one_g02_phase_certificate_extract(const uint8_t *src, size_t n,
                                      uint64_t out_hash[ONE_WITNESSES],
                                      uint32_t out_pos[ONE_WITNESSES]) {
    if (!src || !out_hash || !out_pos) return -1;
    one_phase_witness w[ONE_WITNESSES];
    uint64_t words = 0;
    uint32_t count = build_witnesses(src, n, w, &words);
    for (uint32_t i = 0; i < count; ++i) {
        out_hash[i] = w[i].hash; out_pos[i] = w[i].pos;
    }
    return (int)count;
}

static int phase_nominate(const uint8_t *src, const uint8_t *dst, size_t n,
                          uint64_t *source_words, uint64_t *target_words,
                          uint64_t *exact_word_compares) {
    one_phase_witness w[ONE_WITNESSES];
    uint32_t count = build_witnesses(src, n, w, source_words);
    if (!count || n < ONE_WORD) return 0;
    sort_witnesses(w, count);

    for (size_t pos = 0; pos + ONE_WORD <= n; pos += ONE_STRIDE) {
        uint64_t h = word_hash(dst + pos);
        ++*target_words;
        uint32_t lo = 0, hi = count;
        while (lo < hi) {
            uint32_t mid = lo + ((hi - lo) >> 1);
            if (w[mid].hash < h) lo = mid + 1u; else hi = mid;
        }
        for (uint32_t i = lo; i < count && w[i].hash == h; ++i) {
            ++*exact_word_compares;
            if (load_le64(dst + pos) == load_le64(src + w[i].pos)) return 1;
        }
    }
    return 0;
}

static int enabled(const one_g02_relation_result *r) { return r->exact_proofs >= 4; }

static int eager_batch(const uint8_t *packed, size_t relation_len, size_t pair_count) {
    one_g02_relation_result r = {0};
    int checksum = 0;
    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2u) * relation_len;
        const uint8_t *dst = src + relation_len;
        if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &r) < 0) return -1;
        checksum += enabled(&r) ? (int)(r.best_shift + 7) : 1;
    }
    return checksum;
}

static int gated_batch(const uint8_t *packed, size_t relation_len, size_t pair_count) {
    one_g02_relation_result r = {0};
    int checksum = 0;
    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2u) * relation_len;
        const uint8_t *dst = src + relation_len;
        uint64_t sw = 0, tw = 0, ec = 0;
        if (!phase_nominate(src, dst, relation_len, &sw, &tw, &ec)) { checksum += 1; continue; }
        uint64_t gate_reads = 0;
        int fired = one_g02_shift_relation_sparse_gate(src, dst, relation_len, &r, &gate_reads);
        if (fired < 0) return -1;
        checksum += enabled(&r) ? (int)(r.best_shift + 7) : 1;
    }
    return checksum;
}

int one_g02_cold_rescue_measure(const uint8_t *packed, size_t relation_len,
                                size_t pair_count, size_t batch,
                                one_g02_cold_rescue_measurement *m) {
    if (!packed || !m || relation_len < 1024 || !pair_count || !batch) return -1;
    uint64_t t, a1, a2, b1, b2;
    volatile int escape = 0;

    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x = eager_batch(packed, relation_len, pair_count); if (x < 0) return -2; escape ^= x; }
    a1 = now_ns() - t;
    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x = gated_batch(packed, relation_len, pair_count); if (x < 0) return -3; escape ^= x; }
    b1 = now_ns() - t;
    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x = gated_batch(packed, relation_len, pair_count); if (x < 0) return -4; escape ^= x; }
    b2 = now_ns() - t;
    t = now_ns();
    for (size_t k = 0; k < batch; ++k) { int x = eager_batch(packed, relation_len, pair_count); if (x < 0) return -5; escape ^= x; }
    a2 = now_ns() - t;
    (void)escape;

    *m = (one_g02_cold_rescue_measurement){0};
    m->eager_ns_per_batch = ((double)a1 + (double)a2) / (2.0 * (double)batch);
    m->gated_ns_per_batch = ((double)b1 + (double)b2) / (2.0 * (double)batch);
    m->eager_exact_pairs = pair_count;

    for (size_t i = 0; i < pair_count; ++i) {
        const uint8_t *src = packed + (i * 2u) * relation_len;
        const uint8_t *dst = src + relation_len;
        one_g02_relation_result eager = {0}, gated = {0};
        if (one_g02_shift_relation_safe_dispatch(src, dst, relation_len, &eager) < 0) return -6;
        int eager_on = enabled(&eager);
        m->exact_positive_pairs += eager_on ? 1u : 0u;

        uint64_t sw = 0, tw = 0, ec = 0;
        int nominated = phase_nominate(src, dst, relation_len, &sw, &tw, &ec);
        m->phase_source_words += sw;
        m->phase_target_words += tw;
        m->phase_exact_word_compares += ec;
        m->phase_nominations += nominated ? 1u : 0u;
        int fired = 0;
        if (nominated) {
            uint64_t gate_reads = 0;
            fired = one_g02_shift_relation_sparse_gate(src, dst, relation_len, &gated, &gate_reads);
            if (fired < 0) return -7;
            m->sparse_gate_compared_bytes += gate_reads;
            m->sparse_gate_fires += fired ? 1u : 0u;
            m->sparse_gate_rejects += fired ? 0u : 1u;
            m->gated_exact_executions += fired ? 1u : 0u;
        }
        int gated_on = enabled(&gated);
        if (eager_on && gated_on && eager.best_shift == gated.best_shift) ++m->productive_retained;
        if (!eager_on && gated_on) ++m->negative_enabled;
    }
    return 0;
}
