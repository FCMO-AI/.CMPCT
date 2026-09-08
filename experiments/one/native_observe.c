#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define FNV64_OFFSET UINT64_C(0xcbf29ce484222325)
#define FNV64_PRIME  UINT64_C(0x100000001b3)

struct one_run { uint64_t start, length; uint8_t value; };
struct one_reuse { uint64_t source, target, length; };
struct one_stats {
    uint64_t input_bytes, source_scan_bytes, chunk_fingerprints, hash_lookups;
    uint64_t collision_verifications, verification_read_bytes, total_source_read_bytes;
    uint64_t run_candidates, run_opportunity_bytes, reuse_candidates, reuse_opportunity_bytes;
    uint64_t peak_index_entries, retained_index_payload_bytes;
};
struct one_result {
    struct one_run *runs; uint64_t run_count, run_capacity;
    struct one_reuse *reuse; uint64_t reuse_count, reuse_capacity;
    struct one_stats stats;
};
struct slot { uint64_t hash, source; uint8_t used; };

static uint64_t next_pow2(uint64_t v) {
    uint64_t p = 1;
    while (p < v && p <= (UINT64_MAX >> 1)) p <<= 1;
    return p;
}

static int append_run(struct one_result *out, uint64_t start, uint64_t length, uint8_t value) {
    if (out->run_count >= out->run_capacity) return -4;
    out->runs[out->run_count++] = (struct one_run){start, length, value};
    out->stats.run_opportunity_bytes += length;
    return 0;
}
static int append_reuse(struct one_result *out, uint64_t source, uint64_t target, uint64_t length) {
    if (out->reuse_count >= out->reuse_capacity) return -5;
    out->reuse[out->reuse_count++] = (struct one_reuse){source, target, length};
    out->stats.reuse_opportunity_bytes += length;
    return 0;
}
static struct slot *lookup_slot(struct slot *table, uint64_t mask, uint64_t hash) {
    uint64_t pos = hash & mask;
    for (;;) {
        struct slot *s = &table[pos];
        if (!s->used || s->hash == hash) return s;
        pos = (pos + 1) & mask;
    }
}

int one_observe_native(const uint8_t *data, uint64_t n, uint64_t min_run,
                       uint64_t chunk_size, uint64_t max_index_entries,
                       struct one_result *out) {
    if (!out || min_run == 0 || chunk_size == 0 || max_index_entries == 0) return -1;
    memset(out, 0, sizeof(*out));
    out->stats.input_bytes = n;
    out->stats.source_scan_bytes = n;

    uint64_t max_runs = n ? n : 1;
    uint64_t max_reuse = n / chunk_size + 1;
    out->runs = (struct one_run *)calloc((size_t)max_runs, sizeof(struct one_run));
    out->reuse = (struct one_reuse *)calloc((size_t)max_reuse, sizeof(struct one_reuse));
    if (!out->runs || !out->reuse) goto oom;
    out->run_capacity = max_runs;
    out->reuse_capacity = max_reuse;

    uint64_t chunks = n / chunk_size;
    uint64_t entry_cap = chunks < max_index_entries ? chunks : max_index_entries;
    uint64_t table_size = next_pow2(entry_cap ? entry_cap * 2 : 2);
    struct slot *table = (struct slot *)calloc((size_t)table_size, sizeof(struct slot));
    if (!table) goto oom;
    uint64_t mask = table_size - 1;
    uint64_t index_entries = 0;

    uint64_t run_start = 0, run_length = 0;
    uint8_t run_value = n ? data[0] : 0;
    uint64_t chunk_hash = FNV64_OFFSET;
    uint64_t pending_source = 0, pending_target = 0, pending_length = 0;
    int pending = 0;

#define FLUSH_PENDING() do { \
    if (pending && pending_length) { \
        out->stats.collision_verifications++; \
        out->stats.verification_read_bytes += 2 * pending_length; \
        if (memcmp(data + pending_source, data + pending_target, (size_t)pending_length) == 0) { \
            if (append_reuse(out, pending_source, pending_target, pending_length) != 0) { free(table); return -5; } \
        } \
        pending = 0; pending_length = 0; \
    } \
} while (0)

    for (uint64_t position = 0; position < n; ++position) {
        uint8_t value = data[position];
        if (run_length == 0) {
            run_start = position; run_value = value; run_length = 1;
        } else if (value == run_value) {
            run_length++;
        } else {
            if (run_length >= min_run && append_run(out, run_start, run_length, run_value) != 0) { free(table); return -4; }
            run_start = position; run_value = value; run_length = 1;
        }

        chunk_hash ^= value;
        chunk_hash *= FNV64_PRIME;
        if ((position + 1) % chunk_size == 0) {
            uint64_t start = position + 1 - chunk_size;
            uint64_t fingerprint = chunk_hash;
            chunk_hash = FNV64_OFFSET;
            out->stats.chunk_fingerprints++;

            uint64_t gate = min_run > chunk_size ? min_run : chunk_size;
            if (run_length >= gate) { FLUSH_PENDING(); continue; }

            out->stats.hash_lookups++;
            struct slot *slot = lookup_slot(table, mask, fingerprint);
            int matched = 0;
            if (slot->used) {
                uint64_t source = slot->source;
                if (pending && pending_source + pending_length == source && pending_target + pending_length == start) {
                    pending_length += chunk_size;
                } else {
                    FLUSH_PENDING();
                    pending = 1; pending_source = source; pending_target = start; pending_length = chunk_size;
                }
                matched = 1;
            } else {
                FLUSH_PENDING();
            }
            if (!matched && index_entries < max_index_entries) {
                slot->used = 1; slot->hash = fingerprint; slot->source = start;
                index_entries++;
            }
        }
    }
    FLUSH_PENDING();
    if (run_length >= min_run && append_run(out, run_start, run_length, run_value) != 0) { free(table); return -4; }

    out->stats.run_candidates = out->run_count;
    out->stats.reuse_candidates = out->reuse_count;
    out->stats.peak_index_entries = index_entries;
    out->stats.retained_index_payload_bytes = 16 * index_entries;
    out->stats.total_source_read_bytes = n + out->stats.verification_read_bytes;
    free(table);
    return 0;

oom:
    free(out->runs); free(out->reuse);
    memset(out, 0, sizeof(*out));
    return -2;
#undef FLUSH_PENDING
}

void one_observe_free(struct one_result *out) {
    if (!out) return;
    free(out->runs); free(out->reuse);
    memset(out, 0, sizeof(*out));
}
