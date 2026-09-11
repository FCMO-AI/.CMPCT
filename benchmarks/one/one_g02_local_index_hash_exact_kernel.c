#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

/*
 * ONE-G0.2 local nomination-index research kernel.
 *
 * The production/reference local policy keeps at most 64 unique live keys in
 * circular insertion order and returns the sole matching prior start.  Because
 * keys are inserted only on miss, uniqueness is an invariant.  The candidate
 * keeps the same ring as authority and adds a bounded 128-bucket open-addressed
 * locator.  This file is an A/B falsifier, not product ABI.
 */
#define LOCAL_CAP 64u
#define HASH_CAP 128u
#define WINDOW 64u

typedef struct {
    uint64_t key;
    size_t start;
    int used;
} ring_entry;

typedef struct {
    uint64_t key;
    uint8_t slot;
    uint8_t state; /* 0 empty, 1 live, 2 tombstone */
    uint8_t pad[6];
} hash_bucket;

typedef struct {
    uint64_t lookup_events;
    uint64_t hits;
    uint64_t probes;
    uint64_t tombstones_created;
    uint64_t max_probe;
    uint64_t live_entries;
    uint64_t decision_checksum;
    uint64_t state_bytes;
} local_index_result;

static uint64_t mix64(uint64_t x) {
    x ^= x >> 30;
    x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27;
    x *= UINT64_C(0x94d049bb133111eb);
    x ^= x >> 31;
    return x;
}

static uint64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}

static void checksum_decision(local_index_result *out, int hit, size_t prior) {
    uint64_t v = hit ? (UINT64_C(0x9e3779b97f4a7c15) ^ (uint64_t)prior) : UINT64_C(0xd1b54a32d192ed03);
    out->decision_checksum ^= v + UINT64_C(0x9e3779b97f4a7c15) + (out->decision_checksum << 6) + (out->decision_checksum >> 2);
}

static int linear_find(const ring_entry ring[LOCAL_CAP], size_t count, size_t head,
                       uint64_t key, size_t *prior, uint64_t *probes) {
    for (size_t i = 0; i < count; ++i) {
        size_t slot = (head + i) % LOCAL_CAP;
        (*probes)++;
        if (ring[slot].used && ring[slot].key == key) {
            *prior = ring[slot].start;
            return 1;
        }
    }
    return 0;
}

static int hash_find(const hash_bucket table[HASH_CAP], const ring_entry ring[LOCAL_CAP],
                     uint64_t key, size_t *prior, size_t *slot_out,
                     uint64_t *probes, uint64_t *max_probe) {
    size_t base = (size_t)(mix64(key) & (HASH_CAP - 1u));
    uint64_t local = 0;
    for (size_t i = 0; i < HASH_CAP; ++i) {
        size_t b = (base + i) & (HASH_CAP - 1u);
        local++;
        (*probes)++;
        if (table[b].state == 0) {
            if (local > *max_probe) *max_probe = local;
            return 0;
        }
        if (table[b].state == 1 && table[b].key == key) {
            size_t slot = (size_t)table[b].slot;
            if (slot >= LOCAL_CAP || !ring[slot].used || ring[slot].key != key) return -1;
            *prior = ring[slot].start;
            if (slot_out) *slot_out = slot;
            if (local > *max_probe) *max_probe = local;
            return 1;
        }
    }
    if (local > *max_probe) *max_probe = local;
    return -2;
}

static int hash_remove(hash_bucket table[HASH_CAP], const ring_entry ring[LOCAL_CAP],
                       uint64_t key, uint64_t *probes, uint64_t *max_probe) {
    size_t prior = 0, ring_slot = 0;
    int found = hash_find(table, ring, key, &prior, &ring_slot, probes, max_probe);
    if (found <= 0) return -1;
    size_t base = (size_t)(mix64(key) & (HASH_CAP - 1u));
    for (size_t i = 0; i < HASH_CAP; ++i) {
        size_t b = (base + i) & (HASH_CAP - 1u);
        if (table[b].state == 0) return -2;
        if (table[b].state == 1 && table[b].key == key && (size_t)table[b].slot == ring_slot) {
            table[b].state = 2;
            return 0;
        }
    }
    return -3;
}

static int hash_insert(hash_bucket table[HASH_CAP], uint64_t key, size_t ring_slot,
                       uint64_t *probes, uint64_t *max_probe) {
    size_t base = (size_t)(mix64(key) & (HASH_CAP - 1u));
    size_t first_tomb = HASH_CAP;
    uint64_t local = 0;
    for (size_t i = 0; i < HASH_CAP; ++i) {
        size_t b = (base + i) & (HASH_CAP - 1u);
        local++;
        (*probes)++;
        if (table[b].state == 1 && table[b].key == key) return -2;
        if (table[b].state == 2 && first_tomb == HASH_CAP) first_tomb = b;
        if (table[b].state == 0) {
            size_t dst = first_tomb != HASH_CAP ? first_tomb : b;
            table[dst].key = key;
            table[dst].slot = (uint8_t)ring_slot;
            table[dst].state = 1;
            if (local > *max_probe) *max_probe = local;
            return 0;
        }
    }
    if (first_tomb != HASH_CAP) {
        table[first_tomb].key = key;
        table[first_tomb].slot = (uint8_t)ring_slot;
        table[first_tomb].state = 1;
        if (local > *max_probe) *max_probe = local;
        return 0;
    }
    if (local > *max_probe) *max_probe = local;
    return -3;
}

static int linear_event(ring_entry ring[LOCAL_CAP], size_t *count, size_t *head,
                        uint64_t key, size_t start, local_index_result *out) {
    size_t prior = 0;
    int hit = linear_find(ring, *count, *head, key, &prior, &out->probes);
    out->lookup_events++;
    if (hit) out->hits++;
    checksum_decision(out, hit, prior);
    if (!hit) {
        size_t slot;
        if (*count < LOCAL_CAP) {
            slot = (*head + *count) % LOCAL_CAP;
            (*count)++;
        } else {
            slot = *head;
            *head = (*head + 1) % LOCAL_CAP;
        }
        ring[slot].key = key;
        ring[slot].start = start;
        ring[slot].used = 1;
    }
    out->live_entries = *count;
    return 0;
}

static int hash_event(ring_entry ring[LOCAL_CAP], hash_bucket table[HASH_CAP],
                      size_t *count, size_t *head, uint64_t key, size_t start,
                      local_index_result *out) {
    size_t prior = 0, slot_seen = 0;
    int hit = hash_find(table, ring, key, &prior, &slot_seen, &out->probes, &out->max_probe);
    if (hit < 0) return -10;
    out->lookup_events++;
    if (hit) out->hits++;
    checksum_decision(out, hit, prior);
    if (!hit) {
        size_t slot;
        if (*count < LOCAL_CAP) {
            slot = (*head + *count) % LOCAL_CAP;
            (*count)++;
        } else {
            slot = *head;
            uint64_t old_key = ring[slot].key;
            if (hash_remove(table, ring, old_key, &out->probes, &out->max_probe) != 0) return -11;
            out->tombstones_created++;
            *head = (*head + 1) % LOCAL_CAP;
        }
        ring[slot].key = key;
        ring[slot].start = start;
        ring[slot].used = 1;
        if (hash_insert(table, key, slot, &out->probes, &out->max_probe) != 0) return -12;
    }
    out->live_entries = *count;
    return 0;
}

static int scan_linear(const uint8_t *data, size_t length, const uint64_t gear[256], local_index_result *out) {
    ring_entry ring[LOCAL_CAP] = {{0}};
    size_t count = 0, head = 0;
    uint64_t h = 0;
    uint8_t run_value = length ? data[0] : 0;
    size_t run_length = 0;
    *out = (local_index_result){0};
    out->state_bytes = sizeof(ring);
    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (!run_length) { run_value = value; run_length = 1; }
        else if (value == run_value) run_length++;
        else { run_value = value; run_length = 1; }
        h = (h << 1) + gear[value];
        if (position + 1 < WINDOW) continue;
        if (run_length >= WINDOW || ((position + 1) % WINDOW) != 0) continue;
        size_t start = position + 1 - WINDOW;
        if (linear_event(ring, &count, &head, h, start, out) != 0) return -1;
    }
    return 0;
}

static int scan_hash(const uint8_t *data, size_t length, const uint64_t gear[256], local_index_result *out) {
    ring_entry ring[LOCAL_CAP] = {{0}};
    hash_bucket table[HASH_CAP] = {{0}};
    size_t count = 0, head = 0;
    uint64_t h = 0;
    uint8_t run_value = length ? data[0] : 0;
    size_t run_length = 0;
    *out = (local_index_result){0};
    out->state_bytes = sizeof(ring) + sizeof(table);
    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (!run_length) { run_value = value; run_length = 1; }
        else if (value == run_value) run_length++;
        else { run_value = value; run_length = 1; }
        h = (h << 1) + gear[value];
        if (position + 1 < WINDOW) continue;
        if (run_length >= WINDOW || ((position + 1) % WINDOW) != 0) continue;
        size_t start = position + 1 - WINDOW;
        if (hash_event(ring, table, &count, &head, h, start, out) != 0) return -2;
    }
    return 0;
}

int one_g02_local_index_hash_audit(const uint8_t *data, size_t length, const uint64_t gear[256],
                                   local_index_result *baseline, local_index_result *candidate) {
    if ((!data && length) || !gear || !baseline || !candidate) return -1;
    if (scan_linear(data, length, gear, baseline) != 0) return -2;
    if (scan_hash(data, length, gear, candidate) != 0) return -3;
    if (baseline->lookup_events != candidate->lookup_events ||
        baseline->hits != candidate->hits ||
        baseline->live_entries != candidate->live_entries ||
        baseline->decision_checksum != candidate->decision_checksum) return -4;
    return 0;
}

int one_g02_local_index_hash_key_stream_audit(const uint64_t *keys, size_t count_keys,
                                              local_index_result *baseline, local_index_result *candidate) {
    if ((!keys && count_keys) || !baseline || !candidate) return -1;
    ring_entry br[LOCAL_CAP] = {{0}}, cr[LOCAL_CAP] = {{0}};
    hash_bucket table[HASH_CAP] = {{0}};
    size_t bc = 0, bh = 0, cc = 0, ch = 0;
    *baseline = (local_index_result){0};
    *candidate = (local_index_result){0};
    baseline->state_bytes = sizeof(br);
    candidate->state_bytes = sizeof(cr) + sizeof(table);
    for (size_t i = 0; i < count_keys; ++i) {
        if (linear_event(br, &bc, &bh, keys[i], i * WINDOW, baseline) != 0) return -2;
        if (hash_event(cr, table, &cc, &ch, keys[i], i * WINDOW, candidate) != 0) return -3;
        if (bc != cc || baseline->hits != candidate->hits ||
            baseline->decision_checksum != candidate->decision_checksum) return -4;
    }
    return 0;
}

int one_g02_local_index_hash_measure(const uint8_t *data, size_t length, const uint64_t gear[256],
                                     size_t batch, double *baseline_ns, double *candidate_ns,
                                     local_index_result *baseline, local_index_result *candidate) {
    if ((!data && length) || !gear || !batch || !baseline_ns || !candidate_ns || !baseline || !candidate) return -1;
    local_index_result br = {0}, cr = {0};
    if (one_g02_local_index_hash_audit(data, length, gear, &br, &cr) != 0) return -2;
    uint64_t t, b1, b2, c1, c2;
    t = now_ns(); for (size_t i = 0; i < batch; ++i) if (scan_linear(data, length, gear, &br) != 0) return -3; b1 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; ++i) if (scan_hash(data, length, gear, &cr) != 0) return -4; c1 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; ++i) if (scan_hash(data, length, gear, &cr) != 0) return -5; c2 = now_ns() - t;
    t = now_ns(); for (size_t i = 0; i < batch; ++i) if (scan_linear(data, length, gear, &br) != 0) return -6; b2 = now_ns() - t;
    *baseline_ns = ((double)b1 + (double)b2) / (2.0 * (double)batch);
    *candidate_ns = ((double)c1 + (double)c2) / (2.0 * (double)batch);
    *baseline = br;
    *candidate = cr;
    return 0;
}
