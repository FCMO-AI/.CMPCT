#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define ONE_G02_CERT_WINDOW 32u
#define ONE_G02_CERT_K 8u
#define ONE_G02_OBS_WINDOW 64u
#define ONE_G02_ANCHOR_MASK 1023u
#define ONE_G02_CERT_STATE_BYTES 136u

typedef struct {
    uint64_t anchors;
    uint64_t qualifying_runs;
    uint64_t observer_sink;
    uint64_t certificate_windows;
    uint64_t certificate_hash_checks;
    uint64_t certificate_exact_compares;
    uint64_t certificate_nominations;
    uint64_t certificate_state_bytes;
} one_g02_certificate_probe_result;

typedef struct {
    uint64_t hash[ONE_G02_CERT_K];
    uint32_t pos[ONE_G02_CERT_K];
    uint8_t count;
    uint8_t max_index;
} one_g02_bottom8;

static uint64_t rotl64(uint64_t x, unsigned amount) {
    amount &= 63u;
    return (x << amount) | (x >> ((64u - amount) & 63u));
}

static void bottom8_recompute_max(one_g02_bottom8 *b) {
    uint8_t m = 0u;
    for (uint8_t i = 1u; i < b->count; ++i) {
        if (b->hash[i] > b->hash[m] ||
            (b->hash[i] == b->hash[m] && b->pos[i] > b->pos[m])) {
            m = i;
        }
    }
    b->max_index = m;
}

static void bottom8_offer(one_g02_bottom8 *b, uint64_t h, uint32_t pos) {
    if (b->count < ONE_G02_CERT_K) {
        const uint8_t i = b->count++;
        b->hash[i] = h;
        b->pos[i] = pos;
        bottom8_recompute_max(b);
        return;
    }
    const uint8_t m = b->max_index;
    if (h < b->hash[m] || (h == b->hash[m] && pos < b->pos[m])) {
        b->hash[m] = h;
        b->pos[m] = pos;
        bottom8_recompute_max(b);
    }
}

static void observe_baseline_object(const uint8_t *data, size_t n, const uint64_t *gear,
                                    one_g02_certificate_probe_result *out) {
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
        if (i + 1u >= ONE_G02_OBS_WINDOW && (h & ONE_G02_ANCHOR_MASK) == 0u) {
            ++out->anchors;
            out->observer_sink ^= h + (uint64_t)i;
        }
    }
    if (run_length >= 8u) out->qualifying_runs += run_length;
    out->observer_sink ^= h;
}

static void observe_candidate_source(const uint8_t *data, size_t n, const uint64_t *gear,
                                     one_g02_bottom8 *cert,
                                     one_g02_certificate_probe_result *out) {
    if (n == 0u) return;
    uint64_t obs_h = 0u;
    uint64_t cert_h = 0u;
    uint8_t ring[ONE_G02_CERT_WINDOW] = {0};
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
        obs_h = (obs_h << 1) + gear[v];
        if (i + 1u >= ONE_G02_OBS_WINDOW && (obs_h & ONE_G02_ANCHOR_MASK) == 0u) {
            ++out->anchors;
            out->observer_sink ^= obs_h + (uint64_t)i;
        }

        if (i < ONE_G02_CERT_WINDOW) {
            ring[i] = v;
            cert_h = rotl64(cert_h, 1u) ^ gear[v];
            if (i + 1u == ONE_G02_CERT_WINDOW) {
                ++out->certificate_windows;
                bottom8_offer(cert, cert_h, 0u);
            }
        } else {
            const size_t slot = i % ONE_G02_CERT_WINDOW;
            const uint8_t old = ring[slot];
            ring[slot] = v;
            cert_h = rotl64(cert_h, 1u) ^ rotl64(gear[old], ONE_G02_CERT_WINDOW) ^ gear[v];
            ++out->certificate_windows;
            bottom8_offer(cert, cert_h, (uint32_t)(i + 1u - ONE_G02_CERT_WINDOW));
        }
    }
    if (run_length >= 8u) out->qualifying_runs += run_length;
    out->observer_sink ^= obs_h;
}

static void observe_candidate_target(const uint8_t *source, const uint8_t *target, size_t n,
                                     const uint64_t *gear, const one_g02_bottom8 *cert,
                                     one_g02_certificate_probe_result *out) {
    if (n == 0u) return;
    uint64_t obs_h = 0u;
    uint64_t cert_h = 0u;
    uint8_t ring[ONE_G02_CERT_WINDOW] = {0};
    uint8_t run_value = target[0];
    size_t run_length = 0u;
    for (size_t i = 0u; i < n; ++i) {
        const uint8_t v = target[i];
        if (run_length == 0u || v != run_value) {
            if (run_length >= 8u) out->qualifying_runs += run_length;
            run_value = v;
            run_length = 1u;
        } else {
            ++run_length;
        }
        obs_h = (obs_h << 1) + gear[v];
        if (i + 1u >= ONE_G02_OBS_WINDOW && (obs_h & ONE_G02_ANCHOR_MASK) == 0u) {
            ++out->anchors;
            out->observer_sink ^= obs_h + (uint64_t)i;
        }

        if (i < ONE_G02_CERT_WINDOW) {
            ring[i] = v;
            cert_h = rotl64(cert_h, 1u) ^ gear[v];
            if (i + 1u < ONE_G02_CERT_WINDOW) continue;
        } else {
            const size_t slot = i % ONE_G02_CERT_WINDOW;
            const uint8_t old = ring[slot];
            ring[slot] = v;
            cert_h = rotl64(cert_h, 1u) ^ rotl64(gear[old], ONE_G02_CERT_WINDOW) ^ gear[v];
        }
        ++out->certificate_windows;
        const size_t target_pos = i + 1u - ONE_G02_CERT_WINDOW;
        for (uint8_t j = 0u; j < cert->count; ++j) {
            ++out->certificate_hash_checks;
            if (cert_h != cert->hash[j]) continue;
            ++out->certificate_exact_compares;
            const size_t source_pos = cert->pos[j];
            if (source_pos + ONE_G02_CERT_WINDOW <= n &&
                memcmp(source + source_pos, target + target_pos, ONE_G02_CERT_WINDOW) == 0) {
                ++out->certificate_nominations;
                out->observer_sink ^= cert_h ^ (uint64_t)target_pos;
                return;
            }
        }
    }
    if (run_length >= 8u) out->qualifying_runs += run_length;
    out->observer_sink ^= obs_h;
}

int one_g02_certificate_probe_baseline(const uint8_t *source, const uint8_t *target, size_t n,
                                       const uint64_t *gear,
                                       one_g02_certificate_probe_result *out) {
    if (!source || !target || !gear || !out) return -1;
    memset(out, 0, sizeof(*out));
    observe_baseline_object(source, n, gear, out);
    observe_baseline_object(target, n, gear, out);
    return 0;
}

int one_g02_certificate_probe_candidate(const uint8_t *source, const uint8_t *target, size_t n,
                                        const uint64_t *gear,
                                        one_g02_certificate_probe_result *out) {
    if (!source || !target || !gear || !out) return -1;
    memset(out, 0, sizeof(*out));
    one_g02_bottom8 cert;
    memset(&cert, 0, sizeof(cert));
    observe_candidate_source(source, n, gear, &cert, out);
    const uint64_t baseline_anchors = out->anchors;
    const uint64_t baseline_runs = out->qualifying_runs;
    observe_candidate_target(source, target, n, gear, &cert, out);
    (void)baseline_anchors;
    (void)baseline_runs;
    out->certificate_state_bytes = ONE_G02_CERT_STATE_BYTES;
    return 0;
}
