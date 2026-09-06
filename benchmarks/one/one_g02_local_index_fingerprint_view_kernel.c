#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define LOCAL_CAP 64u
#define FP_CAP 128u
#define WINDOW 64u

typedef struct { uint64_t key; size_t start; int used; } ring_entry;
typedef struct {
    uint64_t lookup_events, hits, full_key_checks, fingerprint_bytes;
    uint64_t live_entries, decision_checksum, state_bytes;
} local_index_result;

static uint64_t now_ns(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}
static void decision(local_index_result *o, int hit, size_t prior) {
    uint64_t v = hit ? (UINT64_C(0x9e3779b97f4a7c15) ^ (uint64_t)prior) : UINT64_C(0xd1b54a32d192ed03);
    o->decision_checksum ^= v + UINT64_C(0x9e3779b97f4a7c15) + (o->decision_checksum << 6) + (o->decision_checksum >> 2);
}
static uint8_t fingerprint(uint64_t key) { return (uint8_t)(key >> 56); }

static int linear_find(const ring_entry r[LOCAL_CAP], size_t count, size_t head,
                       uint64_t key, size_t *prior, local_index_result *o) {
    for (size_t i = 0; i < count; i++) {
        size_t s = (head + i) & (LOCAL_CAP - 1u);
        o->full_key_checks++;
        if (r[s].used && r[s].key == key) { *prior = r[s].start; return 1; }
    }
    return 0;
}

static int fp_find(const ring_entry r[LOCAL_CAP], const uint8_t fp[FP_CAP],
                   size_t count, size_t head, uint64_t key, size_t *prior,
                   local_index_result *o) {
    if (!count) return 0;
    const uint8_t target = fingerprint(key);
    const uint8_t *cur = fp + head;
    const uint8_t *end = cur + count;
    /* Conservative accounting: charge the full logical fingerprint interval. */
    o->fingerprint_bytes += count;
    while (cur < end) {
        const uint8_t *p = (const uint8_t *)memchr(cur, (int)target, (size_t)(end - cur));
        if (!p) return 0;
        size_t s = ((size_t)(p - fp)) & (LOCAL_CAP - 1u);
        o->full_key_checks++;
        if (!r[s].used) return -1;
        if (r[s].key == key) { *prior = r[s].start; return 1; }
        cur = p + 1;
    }
    return 0;
}

static int linear_event(ring_entry r[LOCAL_CAP], size_t *count, size_t *head,
                        uint64_t key, size_t start, local_index_result *o) {
    size_t prior = 0;
    int hit = linear_find(r, *count, *head, key, &prior, o);
    o->lookup_events++;
    if (hit) o->hits++;
    decision(o, hit, prior);
    if (!hit) {
        size_t s;
        if (*count < LOCAL_CAP) { s = (*head + *count) & (LOCAL_CAP - 1u); (*count)++; }
        else { s = *head; *head = (*head + 1u) & (LOCAL_CAP - 1u); }
        r[s].key = key; r[s].start = start; r[s].used = 1;
    }
    o->live_entries = *count;
    return 0;
}

static int fp_event(ring_entry r[LOCAL_CAP], uint8_t fp[FP_CAP], size_t *count, size_t *head,
                    uint64_t key, size_t start, local_index_result *o) {
    size_t prior = 0;
    int hit = fp_find(r, fp, *count, *head, key, &prior, o);
    if (hit < 0) return -1;
    o->lookup_events++;
    if (hit) o->hits++;
    decision(o, hit, prior);
    if (!hit) {
        size_t s;
        if (*count < LOCAL_CAP) { s = (*head + *count) & (LOCAL_CAP - 1u); (*count)++; }
        else { s = *head; *head = (*head + 1u) & (LOCAL_CAP - 1u); }
        r[s].key = key; r[s].start = start; r[s].used = 1;
        uint8_t f = fingerprint(key);
        fp[s] = f;
        fp[s + LOCAL_CAP] = f;
    }
    o->live_entries = *count;
    return 0;
}

static int scan_linear(const uint8_t *d, size_t n, const uint64_t g[256], local_index_result *o) {
    ring_entry r[LOCAL_CAP] = {{0}};
    size_t count = 0, head = 0;
    uint64_t h = 0;
    uint8_t rv = n ? d[0] : 0;
    size_t rl = 0;
    *o = (local_index_result){0}; o->state_bytes = sizeof(r);
    for (size_t p = 0; p < n; p++) {
        uint8_t v = d[p];
        if (!rl) { rv = v; rl = 1; }
        else if (v == rv) rl++;
        else { rv = v; rl = 1; }
        h = (h << 1) + g[v];
        if (p + 1 < WINDOW || rl >= WINDOW || ((p + 1) % WINDOW) != 0) continue;
        if (linear_event(r, &count, &head, h, p + 1 - WINDOW, o) != 0) return -1;
    }
    return 0;
}

static int scan_fp(const uint8_t *d, size_t n, const uint64_t g[256], local_index_result *o) {
    ring_entry r[LOCAL_CAP] = {{0}};
    uint8_t fp[FP_CAP] = {0};
    size_t count = 0, head = 0;
    uint64_t h = 0;
    uint8_t rv = n ? d[0] : 0;
    size_t rl = 0;
    *o = (local_index_result){0}; o->state_bytes = sizeof(r) + sizeof(fp);
    for (size_t p = 0; p < n; p++) {
        uint8_t v = d[p];
        if (!rl) { rv = v; rl = 1; }
        else if (v == rv) rl++;
        else { rv = v; rl = 1; }
        h = (h << 1) + g[v];
        if (p + 1 < WINDOW || rl >= WINDOW || ((p + 1) % WINDOW) != 0) continue;
        if (fp_event(r, fp, &count, &head, h, p + 1 - WINDOW, o) != 0) return -2;
    }
    return 0;
}

static int run_key_stream_linear(const uint64_t *keys, size_t n, local_index_result *o) {
    ring_entry r[LOCAL_CAP] = {{0}};
    size_t count = 0, head = 0;
    *o = (local_index_result){0}; o->state_bytes = sizeof(r);
    for (size_t i = 0; i < n; i++) {
        if (linear_event(r, &count, &head, keys[i], i * WINDOW, o) != 0) return -1;
    }
    return 0;
}

static int run_key_stream_fp(const uint64_t *keys, size_t n, local_index_result *o) {
    ring_entry r[LOCAL_CAP] = {{0}};
    uint8_t fp[FP_CAP] = {0};
    size_t count = 0, head = 0;
    *o = (local_index_result){0}; o->state_bytes = sizeof(r) + sizeof(fp);
    for (size_t i = 0; i < n; i++) {
        if (fp_event(r, fp, &count, &head, keys[i], i * WINDOW, o) != 0) return -1;
    }
    return 0;
}

int one_g02_local_index_fp_audit(const uint8_t *d, size_t n, const uint64_t g[256],
                                 local_index_result *b, local_index_result *c) {
    if ((!d && n) || !g || !b || !c) return -1;
    if (scan_linear(d, n, g, b) != 0) return -2;
    if (scan_fp(d, n, g, c) != 0) return -3;
    return (b->lookup_events == c->lookup_events && b->hits == c->hits &&
            b->live_entries == c->live_entries && b->decision_checksum == c->decision_checksum) ? 0 : -4;
}

int one_g02_local_index_fp_key_stream_audit(const uint64_t *keys, size_t n,
                                            local_index_result *b, local_index_result *c) {
    if ((!keys && n) || !b || !c) return -1;
    if (run_key_stream_linear(keys, n, b) != 0) return -2;
    if (run_key_stream_fp(keys, n, c) != 0) return -3;
    return (b->lookup_events == c->lookup_events && b->hits == c->hits &&
            b->live_entries == c->live_entries && b->decision_checksum == c->decision_checksum) ? 0 : -4;
}

int one_g02_local_index_fp_key_stream_measure(const uint64_t *keys, size_t n, size_t batch,
                                              double *bn, double *cn,
                                              local_index_result *b, local_index_result *c) {
    if ((!keys && n) || !batch || !bn || !cn || !b || !c) return -1;
    local_index_result br = {0}, cr = {0};
    if (one_g02_local_index_fp_key_stream_audit(keys, n, &br, &cr) != 0) return -2;
    uint64_t t, b1, b2, c1, c2;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (run_key_stream_linear(keys, n, &br) != 0) return -3; b1 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (run_key_stream_fp(keys, n, &cr) != 0) return -4; c1 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (run_key_stream_fp(keys, n, &cr) != 0) return -5; c2 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (run_key_stream_linear(keys, n, &br) != 0) return -6; b2 = now_ns() - t;
    *bn = ((double)b1 + (double)b2) / (2.0 * (double)batch);
    *cn = ((double)c1 + (double)c2) / (2.0 * (double)batch);
    *b = br; *c = cr;
    return 0;
}

int one_g02_local_index_fp_measure(const uint8_t *d, size_t n, const uint64_t g[256], size_t batch,
                                   double *bn, double *cn, local_index_result *b, local_index_result *c) {
    if ((!d && n) || !g || !batch || !bn || !cn || !b || !c) return -1;
    local_index_result br = {0}, cr = {0};
    if (one_g02_local_index_fp_audit(d, n, g, &br, &cr) != 0) return -2;
    uint64_t t, b1, b2, c1, c2;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (scan_linear(d, n, g, &br) != 0) return -3; b1 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (scan_fp(d, n, g, &cr) != 0) return -4; c1 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (scan_fp(d, n, g, &cr) != 0) return -5; c2 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; i++) if (scan_linear(d, n, g, &br) != 0) return -6; b2 = now_ns() - t;
    *bn = ((double)b1 + (double)b2) / (2.0 * (double)batch);
    *cn = ((double)c1 + (double)c2) / (2.0 * (double)batch);
    *b = br; *c = cr;
    return 0;
}
