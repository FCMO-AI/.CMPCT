#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define ONE_CERT_WINDOW 32u
#define ONE_CERT_K 8u
#define ONE_OBS_WINDOW 64u
#define ONE_ANCHOR_MASK 1023u
#define ONE_CERT_RETAINED_BYTES 98u
#define ONE_CERT_SCRATCH_BYTES (ONE_CERT_WINDOW * sizeof(uint64_t))

typedef struct {
    uint64_t anchors;
    uint64_t qualifying_runs;
    uint64_t observer_sink;
    uint64_t certificate_windows;
    uint64_t certificate_threshold_passes;
    uint64_t certificate_hash_checks;
    uint64_t certificate_exact_compares;
    uint64_t certificate_nominations;
    uint64_t retained_state_bytes;
    uint64_t scratch_state_bytes;
} one_cert_result;

typedef struct {
    uint64_t hash[ONE_CERT_K];
    uint32_t pos[ONE_CERT_K];
    uint8_t count;
    uint8_t max_index;
} one_bottom8;

static void bottom8_recompute_max(one_bottom8 *b) {
    uint8_t m = 0u;
    for (uint8_t i = 1u; i < b->count; ++i) {
        if (b->hash[i] > b->hash[m] ||
            (b->hash[i] == b->hash[m] && b->pos[i] > b->pos[m])) m = i;
    }
    b->max_index = m;
}

static void bottom8_offer(one_bottom8 *b, uint64_t h, uint32_t pos) {
    if (b->count < ONE_CERT_K) {
        const uint8_t i = b->count++;
        b->hash[i] = h;
        b->pos[i] = pos;
        bottom8_recompute_max(b);
        return;
    }
    const uint8_t m = b->max_index;
    if (h > b->hash[m] || (h == b->hash[m] && pos >= b->pos[m])) return;
    b->hash[m] = h;
    b->pos[m] = pos;
    bottom8_recompute_max(b);
}

static void observe_only(const uint8_t *data, size_t n, const uint64_t *gear,
                         one_cert_result *out) {
    if (n == 0u) return;
    uint64_t h = 0u;
    uint8_t run_value = data[0];
    size_t run_length = 0u;
    for (size_t i = 0u; i < n; ++i) {
        const uint8_t v = data[i];
        if (run_length == 0u || v != run_value) {
            if (run_length >= 8u) out->qualifying_runs += run_length;
            run_value = v;
            run_length = 1u;
        } else {
            ++run_length;
        }
        h = (h << 1) + gear[v];
        if (i + 1u >= ONE_OBS_WINDOW && (h & ONE_ANCHOR_MASK) == 0u) {
            ++out->anchors;
            out->observer_sink ^= h + (uint64_t)i;
        }
    }
    if (run_length >= 8u) out->qualifying_runs += run_length;
    out->observer_sink ^= h;
}

static void candidate_source(const uint8_t *data, size_t n, const uint64_t *gear,
                             one_bottom8 *cert, one_cert_result *out) {
    if (n == 0u) return;
    uint64_t h = 0u;
    uint64_t delayed[ONE_CERT_WINDOW] = {0};
    uint8_t run_value = data[0];
    size_t run_length = 0u;
    for (size_t i = 0u; i < n; ++i) {
        const uint8_t v = data[i];
        if (run_length == 0u || v != run_value) {
            if (run_length >= 8u) out->qualifying_runs += run_length;
            run_value = v;
            run_length = 1u;
        } else {
            ++run_length;
        }
        const size_t slot = i & (ONE_CERT_WINDOW - 1u);
        const uint64_t old_h = delayed[slot];
        h = (h << 1) + gear[v];
        delayed[slot] = h;
        if (i + 1u >= ONE_OBS_WINDOW && (h & ONE_ANCHOR_MASK) == 0u) {
            ++out->anchors;
            out->observer_sink ^= h + (uint64_t)i;
        }
        if (i + 1u >= ONE_CERT_WINDOW) {
            const uint64_t local = h - (old_h << ONE_CERT_WINDOW);
            ++out->certificate_windows;
            bottom8_offer(cert, local, (uint32_t)(i + 1u - ONE_CERT_WINDOW));
        }
    }
    if (run_length >= 8u) out->qualifying_runs += run_length;
    out->observer_sink ^= h;
}

static void candidate_target(const uint8_t *source, const uint8_t *target, size_t n,
                             const uint64_t *gear, const one_bottom8 *cert,
                             one_cert_result *out) {
    if (n == 0u) return;
    uint64_t h = 0u;
    uint64_t delayed[ONE_CERT_WINDOW] = {0};
    uint8_t run_value = target[0];
    size_t run_length = 0u;
    int nominated = 0;
    for (size_t i = 0u; i < n; ++i) {
        const uint8_t v = target[i];
        if (run_length == 0u || v != run_value) {
            if (run_length >= 8u) out->qualifying_runs += run_length;
            run_value = v;
            run_length = 1u;
        } else {
            ++run_length;
        }
        const size_t slot = i & (ONE_CERT_WINDOW - 1u);
        const uint64_t old_h = delayed[slot];
        h = (h << 1) + gear[v];
        delayed[slot] = h;
        if (i + 1u >= ONE_OBS_WINDOW && (h & ONE_ANCHOR_MASK) == 0u) {
            ++out->anchors;
            out->observer_sink ^= h + (uint64_t)i;
        }
        if (nominated || i + 1u < ONE_CERT_WINDOW) continue;
        const uint64_t local = h - (old_h << ONE_CERT_WINDOW);
        ++out->certificate_windows;
        if (cert->count == 0u) continue;
        if (cert->count == ONE_CERT_K && local > cert->hash[cert->max_index]) continue;
        ++out->certificate_threshold_passes;
        const size_t target_pos = i + 1u - ONE_CERT_WINDOW;
        for (uint8_t j = 0u; j < cert->count; ++j) {
            ++out->certificate_hash_checks;
            if (local != cert->hash[j]) continue;
            ++out->certificate_exact_compares;
            const size_t source_pos = cert->pos[j];
            if (source_pos + ONE_CERT_WINDOW <= n &&
                memcmp(source + source_pos, target + target_pos, ONE_CERT_WINDOW) == 0) {
                ++out->certificate_nominations;
                nominated = 1;
                break;
            }
        }
    }
    if (run_length >= 8u) out->qualifying_runs += run_length;
    out->observer_sink ^= h;
}

int one_observer_derived_baseline(const uint8_t *source, const uint8_t *target, size_t n,
                                  const uint64_t *gear, one_cert_result *out) {
    if (!source || !target || !gear || !out) return -1;
    memset(out, 0, sizeof(*out));
    observe_only(source, n, gear, out);
    observe_only(target, n, gear, out);
    return 0;
}

int one_observer_derived_candidate(const uint8_t *source, const uint8_t *target, size_t n,
                                   const uint64_t *gear, one_cert_result *out) {
    if (!source || !target || !gear || !out) return -1;
    memset(out, 0, sizeof(*out));
    one_bottom8 cert;
    memset(&cert, 0, sizeof(cert));
    candidate_source(source, n, gear, &cert, out);
    candidate_target(source, target, n, gear, &cert, out);
    out->retained_state_bytes = ONE_CERT_RETAINED_BYTES;
    out->scratch_state_bytes = ONE_CERT_SCRATCH_BYTES;
    return 0;
}
