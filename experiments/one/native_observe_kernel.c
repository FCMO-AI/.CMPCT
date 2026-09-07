#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define FNV64_OFFSET UINT64_C(0xcbf29ce484222325)
#define FNV64_PRIME UINT64_C(0x100000001b3)

typedef struct {
    uint64_t start;
    uint64_t length;
    uint64_t value;
} one_run_t;

typedef struct {
    uint64_t source;
    uint64_t target;
    uint64_t length;
} one_reuse_t;

typedef struct {
    uint64_t input_bytes;
    uint64_t source_scan_bytes;
    uint64_t chunk_fingerprints;
    uint64_t hash_lookups;
    uint64_t collision_verifications;
    uint64_t verification_read_bytes;
    uint64_t total_source_read_bytes;
    uint64_t run_candidates;
    uint64_t run_opportunity_bytes;
    uint64_t reuse_candidates;
    uint64_t reuse_opportunity_bytes;
    uint64_t peak_index_entries;
    uint64_t retained_index_payload_bytes;
} one_observe_stats_t;

typedef struct {
    uint64_t key;
    uint64_t source;
    uint8_t occupied;
} one_index_slot_t;

static size_t next_pow2(size_t value) {
    size_t result = 1;
    while (result < value && result <= (SIZE_MAX >> 1)) {
        result <<= 1;
    }
    return result;
}

static size_t mix_slot(uint64_t key, size_t mask) {
    key ^= key >> 33;
    key *= UINT64_C(0xff51afd7ed558ccd);
    key ^= key >> 33;
    key *= UINT64_C(0xc4ceb9fe1a85ec53);
    key ^= key >> 33;
    return (size_t)key & mask;
}

static int index_find(
    const one_index_slot_t *table,
    size_t capacity,
    uint64_t key,
    uint64_t *source
) {
    const size_t mask = capacity - 1;
    size_t slot = mix_slot(key, mask);
    for (size_t probes = 0; probes < capacity; ++probes) {
        const one_index_slot_t *entry = &table[slot];
        if (!entry->occupied) {
            return 0;
        }
        if (entry->key == key) {
            *source = entry->source;
            return 1;
        }
        slot = (slot + 1) & mask;
    }
    return 0;
}

static int index_insert_first(
    one_index_slot_t *table,
    size_t capacity,
    uint64_t key,
    uint64_t source
) {
    const size_t mask = capacity - 1;
    size_t slot = mix_slot(key, mask);
    for (size_t probes = 0; probes < capacity; ++probes) {
        one_index_slot_t *entry = &table[slot];
        if (!entry->occupied) {
            entry->occupied = 1;
            entry->key = key;
            entry->source = source;
            return 1;
        }
        if (entry->key == key) {
            return 0;
        }
        slot = (slot + 1) & mask;
    }
    return 0;
}

static int flush_pending(
    const uint8_t *data,
    uint64_t *pending_source,
    uint64_t *pending_target,
    uint64_t *pending_length,
    one_reuse_t *reuse_out,
    size_t reuse_capacity,
    size_t *reuse_count,
    one_observe_stats_t *stats
) {
    if (*pending_length == 0) {
        return 0;
    }
    stats->collision_verifications += 1;
    stats->verification_read_bytes += 2 * (*pending_length);
    if (memcmp(
            data + (size_t)(*pending_source),
            data + (size_t)(*pending_target),
            (size_t)(*pending_length)
        ) == 0) {
        if (*reuse_count >= reuse_capacity) {
            return -3;
        }
        reuse_out[*reuse_count].source = *pending_source;
        reuse_out[*reuse_count].target = *pending_target;
        reuse_out[*reuse_count].length = *pending_length;
        *reuse_count += 1;
        stats->reuse_opportunity_bytes += *pending_length;
    }
    *pending_source = 0;
    *pending_target = 0;
    *pending_length = 0;
    return 0;
}

int one_observe_native(
    const uint8_t *data,
    size_t length,
    uint64_t min_run,
    uint64_t chunk_size,
    uint64_t max_index_entries,
    one_run_t *runs_out,
    size_t runs_capacity,
    size_t *runs_count_out,
    one_reuse_t *reuse_out,
    size_t reuse_capacity,
    size_t *reuse_count_out,
    one_observe_stats_t *stats
) {
    if (stats == NULL || runs_count_out == NULL || reuse_count_out == NULL) {
        return -1;
    }
    memset(stats, 0, sizeof(*stats));
    *runs_count_out = 0;
    *reuse_count_out = 0;
    if ((length > 0 && data == NULL) || min_run == 0 || chunk_size == 0 || max_index_entries == 0) {
        return -1;
    }

    stats->input_bytes = (uint64_t)length;
    stats->source_scan_bytes = (uint64_t)length;
    if (length == 0) {
        return 0;
    }

    const size_t full_chunks = length / (size_t)chunk_size;
    size_t desired_entries = full_chunks;
    if (desired_entries > (size_t)max_index_entries) {
        desired_entries = (size_t)max_index_entries;
    }
    size_t table_capacity = next_pow2(desired_entries * 2 + 2);
    if (table_capacity < 4) {
        table_capacity = 4;
    }
    one_index_slot_t *table = (one_index_slot_t *)calloc(table_capacity, sizeof(one_index_slot_t));
    if (table == NULL) {
        return -2;
    }

    size_t run_count = 0;
    size_t reuse_count = 0;
    uint64_t index_entries = 0;
    uint64_t run_start = 0;
    uint8_t run_value = data[0];
    uint64_t run_length = 0;
    uint64_t chunk_hash = FNV64_OFFSET;
    uint64_t pending_source = 0;
    uint64_t pending_target = 0;
    uint64_t pending_length = 0;
    const uint64_t run_gate_threshold = min_run > chunk_size ? min_run : chunk_size;

    for (size_t position = 0; position < length; ++position) {
        const uint8_t value = data[position];
        if (run_length == 0) {
            run_start = (uint64_t)position;
            run_value = value;
            run_length = 1;
        } else if (value == run_value) {
            run_length += 1;
        } else {
            if (run_length >= min_run) {
                if (run_count >= runs_capacity) {
                    free(table);
                    return -3;
                }
                runs_out[run_count].start = run_start;
                runs_out[run_count].length = run_length;
                runs_out[run_count].value = run_value;
                run_count += 1;
                stats->run_opportunity_bytes += run_length;
            }
            run_start = (uint64_t)position;
            run_value = value;
            run_length = 1;
        }

        chunk_hash ^= (uint64_t)value;
        chunk_hash *= FNV64_PRIME;
        if (((uint64_t)position + 1) % chunk_size == 0) {
            const uint64_t start = (uint64_t)position + 1 - chunk_size;
            const uint64_t fingerprint = chunk_hash;
            chunk_hash = FNV64_OFFSET;
            stats->chunk_fingerprints += 1;

            if (run_length >= run_gate_threshold) {
                int rc = flush_pending(
                    data, &pending_source, &pending_target, &pending_length,
                    reuse_out, reuse_capacity, &reuse_count, stats
                );
                if (rc != 0) {
                    free(table);
                    return rc;
                }
                continue;
            }

            stats->hash_lookups += 1;
            uint64_t source = 0;
            const int found = index_find(table, table_capacity, fingerprint, &source);
            if (found) {
                if (
                    pending_length > 0 &&
                    pending_source + pending_length == source &&
                    pending_target + pending_length == start
                ) {
                    pending_length += chunk_size;
                } else {
                    int rc = flush_pending(
                        data, &pending_source, &pending_target, &pending_length,
                        reuse_out, reuse_capacity, &reuse_count, stats
                    );
                    if (rc != 0) {
                        free(table);
                        return rc;
                    }
                    pending_source = source;
                    pending_target = start;
                    pending_length = chunk_size;
                }
            } else {
                int rc = flush_pending(
                    data, &pending_source, &pending_target, &pending_length,
                    reuse_out, reuse_capacity, &reuse_count, stats
                );
                if (rc != 0) {
                    free(table);
                    return rc;
                }
                if (index_entries < max_index_entries) {
                    if (index_insert_first(table, table_capacity, fingerprint, start)) {
                        index_entries += 1;
                    }
                }
            }
        }
    }

    int rc = flush_pending(
        data, &pending_source, &pending_target, &pending_length,
        reuse_out, reuse_capacity, &reuse_count, stats
    );
    if (rc != 0) {
        free(table);
        return rc;
    }
    if (run_length >= min_run) {
        if (run_count >= runs_capacity) {
            free(table);
            return -3;
        }
        runs_out[run_count].start = run_start;
        runs_out[run_count].length = run_length;
        runs_out[run_count].value = run_value;
        run_count += 1;
        stats->run_opportunity_bytes += run_length;
    }

    stats->run_candidates = (uint64_t)run_count;
    stats->reuse_candidates = (uint64_t)reuse_count;
    stats->peak_index_entries = index_entries;
    stats->retained_index_payload_bytes = 16 * index_entries;
    stats->total_source_read_bytes = stats->source_scan_bytes + stats->verification_read_bytes;
    *runs_count_out = run_count;
    *reuse_count_out = reuse_count;
    free(table);
    return 0;
}
