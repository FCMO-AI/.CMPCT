#include <stddef.h>
#include <stdint.h>
#include <string.h>

/*
 * ONE-G0.2 semantic bridge: consume an already-proven native minimizer anchor
 * trace entirely in native code while replaying the existing shared-observer
 * pair-nomination policy.  This is intentionally not a fused observer yet:
 * anchor production and event consumption remain separate passes.
 */

#define ONE_G02_WINDOW 64u
#define ONE_G02_PROOF_BLOCK 4096u
#define ONE_G02_MIN_RUN 8u
#define ONE_G02_LOCAL_ENTRIES 64u
#define ONE_G02_GLOBAL_ENTRIES 8192u

typedef struct {
    uint64_t cross_auditions;
    uint64_t cross_exact;
    uint64_t local_peak_entries;
    uint64_t global_peak_entries;
    uint64_t verification_read_bytes;
    uint64_t extension_read_bytes;
    uint64_t anchors_consumed;
} one_g02_nomination_consumer_result;

typedef struct {
    uint64_t key;
    size_t start;
    int used;
} one_g02_index_entry;

static int find_entry(
    const one_g02_index_entry *entries,
    size_t capacity,
    size_t count,
    size_t head,
    uint64_t key,
    size_t *start_out
) {
    for (size_t i = 0; i < count; ++i) {
        const size_t slot = (head + i) % capacity;
        if (entries[slot].used && entries[slot].key == key) {
            *start_out = entries[slot].start;
            return 1;
        }
    }
    return 0;
}

static size_t min_size(size_t a, size_t b) {
    return a < b ? a : b;
}

static size_t extend_left(
    const uint8_t *data,
    size_t source,
    size_t target,
    size_t covered_until,
    uint64_t *reads
) {
    const size_t max_length = min_size(source, target - covered_until);
    size_t matched = 0;
    while (matched < max_length) {
        const size_t step = min_size(ONE_G02_PROOF_BLOCK, max_length - matched);
        const size_t source_start = source - matched - step;
        const size_t target_start = target - matched - step;
        *reads += 2u * (uint64_t)step;
        if (memcmp(data + source_start, data + target_start, step) == 0) {
            matched += step;
            continue;
        }
        for (size_t offset = 1; offset <= step; ++offset) {
            *reads += 2;
            if (data[source - matched - offset] != data[target - matched - offset]) {
                return matched + offset - 1;
            }
        }
        matched += step;
    }
    return matched;
}

static size_t extend_right(
    const uint8_t *data,
    size_t length,
    size_t source,
    size_t target,
    uint64_t *reads
) {
    const size_t max_length = min_size(target - source, length - target);
    size_t matched = ONE_G02_WINDOW;
    while (matched < max_length) {
        const size_t step = min_size(ONE_G02_PROOF_BLOCK, max_length - matched);
        *reads += 2u * (uint64_t)step;
        if (memcmp(data + source + matched, data + target + matched, step) == 0) {
            matched += step;
            continue;
        }
        for (size_t offset = 0; offset < step; ++offset) {
            *reads += 2;
            if (data[source + matched + offset] != data[target + matched + offset]) {
                return matched + offset;
            }
        }
        matched += step;
    }
    return matched;
}

static void audition(
    const uint8_t *data,
    size_t length,
    size_t boundary,
    size_t start,
    int have_prior,
    size_t prior,
    size_t *covered_until,
    one_g02_nomination_consumer_result *out
) {
    if (!have_prior || start < *covered_until) return;

    const int is_cross = prior < boundary && boundary <= start;
    if (is_cross) out->cross_auditions += 1;

    out->verification_read_bytes += 2u * ONE_G02_WINDOW;
    if (memcmp(data + prior, data + start, ONE_G02_WINDOW) != 0) return;

    uint64_t extension_reads = 0;
    const size_t left = extend_left(data, prior, start, *covered_until, &extension_reads);
    const size_t right = extend_right(data, length, prior, start, &extension_reads);
    out->extension_read_bytes += extension_reads;

    const size_t left_start = start - left;
    const size_t target_start = left_start > *covered_until ? left_start : *covered_until;
    const size_t target_end = start + right;
    if (target_end <= target_start) return;

    if (is_cross) out->cross_exact += 1;
    *covered_until = target_end;
}

int one_g02_native_nomination_event_consumer(
    const uint8_t *data,
    size_t length,
    size_t boundary,
    const uint64_t gear[256],
    const uint64_t *anchors,
    size_t anchor_count,
    one_g02_nomination_consumer_result *out
) {
    if (out == NULL || gear == NULL) return -1;
    *out = (one_g02_nomination_consumer_result){0};
    if (length == 0) return anchor_count == 0 ? 0 : -3;
    if (data == NULL || boundary > length || (anchor_count && anchors == NULL)) return -1;

    one_g02_index_entry local[ONE_G02_LOCAL_ENTRIES] = {{0}};
    one_g02_index_entry global[ONE_G02_GLOBAL_ENTRIES] = {{0}};
    size_t local_head = 0, local_count = 0;
    size_t global_count = 0;
    size_t anchor_i = 0;
    size_t covered_until = 0;

    uint64_t h = 0;
    uint8_t run_value = data[0];
    size_t run_length = 0;

    for (size_t position = 0; position < length; ++position) {
        const uint8_t value = data[position];
        if (run_length == 0) {
            run_value = value;
            run_length = 1;
        } else if (value == run_value) {
            run_length += 1;
        } else {
            run_value = value;
            run_length = 1;
        }

        h = (h << 1) + gear[value];
        if (position + 1 < ONE_G02_WINDOW) continue;
        const size_t start = position + 1 - ONE_G02_WINDOW;
        const int run_dominated = run_length >= ONE_G02_WINDOW;

        if (!run_dominated && ((position + 1) % ONE_G02_WINDOW) == 0) {
            size_t prior = 0;
            const int have_prior = find_entry(
                local, ONE_G02_LOCAL_ENTRIES, local_count, local_head, h, &prior
            );
            audition(data, length, boundary, start, have_prior, prior, &covered_until, out);
            if (!have_prior) {
                size_t slot;
                if (local_count < ONE_G02_LOCAL_ENTRIES) {
                    slot = (local_head + local_count) % ONE_G02_LOCAL_ENTRIES;
                    local_count += 1;
                } else {
                    slot = local_head;
                    local_head = (local_head + 1) % ONE_G02_LOCAL_ENTRIES;
                }
                local[slot].key = h;
                local[slot].start = start;
                local[slot].used = 1;
                if (local_count > out->local_peak_entries) out->local_peak_entries = local_count;
            }
        }

        if (anchor_i < anchor_count) {
            const uint64_t anchor = anchors[anchor_i];
            if (anchor < position) return -4;
            if (anchor == position) {
                size_t prior = 0;
                const int have_prior = find_entry(
                    global, ONE_G02_GLOBAL_ENTRIES, global_count, 0, h, &prior
                );
                audition(data, length, boundary, start, have_prior, prior, &covered_until, out);
                if (!have_prior && global_count < ONE_G02_GLOBAL_ENTRIES) {
                    global[global_count].key = h;
                    global[global_count].start = start;
                    global[global_count].used = 1;
                    global_count += 1;
                    if (global_count > out->global_peak_entries) out->global_peak_entries = global_count;
                }
                anchor_i += 1;
                out->anchors_consumed += 1;
            }
        }
    }

    if (anchor_i != anchor_count) return -5;
    return 0;
}
