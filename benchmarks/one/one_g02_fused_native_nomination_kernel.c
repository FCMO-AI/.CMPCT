#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * ONE-G0.2 research Builder: fuse the already-validated pair-nomination event
 * consumer into the promoted offset-only minimizer pass.  The reader ontology
 * is untouched.  The local first-witness index is fixed and tiny; the global
 * index grows geometrically on demand but retains the exact 8,192-entry cap.
 * This kernel is research evidence, not product ABI.
 */

#define ONE_G02_WINDOW 64u
#define ONE_G02_PROOF_BLOCK 4096u
#define ONE_G02_LOCAL_ENTRIES 64u
#define ONE_G02_GLOBAL_ENTRIES 8192u
#define ONE_G02_GLOBAL_INITIAL_ENTRIES 64u

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads;
    uint64_t cross_auditions;
    uint64_t cross_exact;
    uint64_t local_peak_entries;
    uint64_t global_peak_entries;
    uint64_t verification_read_bytes;
    uint64_t extension_read_bytes;
} one_g02_fused_nomination_result;

typedef struct {
    uint64_t key;
    size_t start;
    int used;
} one_g02_index_entry;

static size_t one_min_size(size_t a, size_t b) { return a < b ? a : b; }

static int find_entry(
    const one_g02_index_entry *entries,
    size_t capacity,
    size_t count,
    size_t head,
    uint64_t key,
    size_t *start_out
) {
    if (count == 0) return 0;
    if (entries == NULL || capacity == 0 || count > capacity) return 0;
    for (size_t i = 0; i < count; ++i) {
        const size_t slot = (head + i) % capacity;
        if (entries[slot].used && entries[slot].key == key) {
            *start_out = entries[slot].start;
            return 1;
        }
    }
    return 0;
}

static size_t extend_left(
    const uint8_t *data,
    size_t source,
    size_t target,
    size_t covered_until,
    uint64_t *reads
) {
    const size_t max_length = one_min_size(source, target - covered_until);
    size_t matched = 0;
    while (matched < max_length) {
        const size_t step = one_min_size(ONE_G02_PROOF_BLOCK, max_length - matched);
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
    const size_t max_length = one_min_size(target - source, length - target);
    size_t matched = ONE_G02_WINDOW;
    while (matched < max_length) {
        const size_t step = one_min_size(ONE_G02_PROOF_BLOCK, max_length - matched);
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
    one_g02_fused_nomination_result *out
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

static int emit_anchor(
    one_g02_fused_nomination_result *out,
    uint64_t anchor,
    uint64_t *trace,
    size_t trace_capacity,
    uint64_t *last_emitted
) {
    if (anchor == *last_emitted) return 0;
    if (trace != NULL) {
        if (out->emitted >= trace_capacity) return -4;
        trace[out->emitted] = anchor;
    }
    *last_emitted = anchor;
    out->emitted += 1;
    return 1;
}

int one_g02_fused_native_nomination(
    const uint8_t *data,
    size_t length,
    size_t boundary,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_fused_nomination_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window != ONE_G02_WINDOW || minimizer_span == 0) return -1;
    if (boundary > length || minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;

    *out = (one_g02_fused_nomination_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    const uint64_t total_states = length >= window ? (uint64_t)(length - window + 1) : 0;
    uint64_t *block_values = NULL;
    uint16_t *suffix_offsets = NULL;
    if (enabled) {
        block_values = (uint64_t *)malloc(4 * block_size * sizeof(uint64_t));
        suffix_offsets = (uint16_t *)malloc(4 * block_size * sizeof(uint16_t));
        if (block_values == NULL || suffix_offsets == NULL) {
            free(block_values);
            free(suffix_offsets);
            return -2;
        }
        out->reserved_state_bytes =
            4 * block_size * sizeof(uint64_t) +
            4 * block_size * sizeof(uint16_t) +
            4 * (sizeof(uint64_t) + sizeof(uint64_t) + sizeof(uint64_t));
    }

    one_g02_index_entry local[ONE_G02_LOCAL_ENTRIES] = {{0}};
    one_g02_index_entry *global = NULL;
    size_t global_capacity = 0;
    size_t local_head = 0, local_count = 0, global_count = 0;
    size_t covered_until = 0;

    uint64_t block_min_value[4] = {0, 0, 0, 0};
    uint64_t block_min_position[4] = {0, 0, 0, 0};
    uint64_t block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    uint64_t suffix_block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};

    uint64_t state = 0;
    uint64_t prefix_value = 0, prefix_position = 0;
    uint64_t middle_value = 0, middle_position = 0;
    uint64_t last_emitted = UINT64_MAX;
    uint64_t states_seen = 0, q = 0;
    size_t r = 0;
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

        state = (state << 1) + gear[value];
        if (position + 1 < window) continue;
        out->positions_considered += 1;

        const size_t start = position + 1 - window;
        const int run_dominated = run_length >= window;
        if (!run_dominated && ((position + 1) % window) == 0) {
            size_t prior = 0;
            const int have_prior = find_entry(
                local, ONE_G02_LOCAL_ENTRIES, local_count, local_head, state, &prior
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
                local[slot].key = state;
                local[slot].start = start;
                local[slot].used = 1;
                if (local_count > out->local_peak_entries) out->local_peak_entries = local_count;
            }
        }

        if (!enabled) continue;
        const size_t slot = (size_t)(q & 3u);
        const size_t base = slot * block_size;
        if (r == 0) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
            if (q >= 3) {
                uint64_t b = q - 3;
                size_t middle_slot = (size_t)(b & 3u);
                if (block_number[middle_slot] != b) goto bad_state;
                middle_value = block_min_value[middle_slot];
                middle_position = block_min_position[middle_slot];
                for (b = q - 2; b <= q - 1; ++b) {
                    middle_slot = (size_t)(b & 3u);
                    if (block_number[middle_slot] != b) goto bad_state;
                    if (block_min_value[middle_slot] <= middle_value) {
                        middle_value = block_min_value[middle_slot];
                        middle_position = block_min_position[middle_slot];
                    }
                }
            }
        } else if (state <= prefix_value) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
        }
        block_values[base + r] = state;

        if (states_seen + 1 >= minimizer_span) {
            uint64_t selected_value = middle_value;
            uint64_t selected_position = middle_position;
            if (prefix_value <= selected_value) {
                selected_value = prefix_value;
                selected_position = prefix_position;
            }
            if (q >= 4 && r + 1 < block_size) {
                const uint64_t old_block = q - 4;
                const size_t old_slot = (size_t)(old_block & 3u);
                if (suffix_block_number[old_slot] != old_block) goto bad_suffix;
                const size_t old_base = old_slot * block_size;
                const size_t idx = old_base + r + 1;
                const uint16_t argmin = suffix_offsets[idx];
                const uint64_t old_value = block_values[old_base + argmin];
                out->suffix_value_indirect_loads += 1;
                if (old_value < selected_value) {
                    selected_value = old_value;
                    selected_position = (uint64_t)(window - 1) + old_block * block_size + argmin;
                }
            }

            const int emitted = emit_anchor(out, selected_position, trace, trace_capacity, &last_emitted);
            if (emitted < 0) goto emit_failure;
            if (emitted > 0) {
                const size_t anchor_start = (size_t)(selected_position + 1 - window);
                size_t prior = 0;
                const int have_prior = find_entry(
                    global, global_capacity, global_count, 0, selected_value, &prior
                );
                audition(data, length, boundary, anchor_start, have_prior, prior, &covered_until, out);
                if (!have_prior && global_count < ONE_G02_GLOBAL_ENTRIES) {
                    if (global_count == global_capacity) {
                        size_t new_capacity = global_capacity == 0
                            ? ONE_G02_GLOBAL_INITIAL_ENTRIES
                            : global_capacity * 2;
                        if (new_capacity > ONE_G02_GLOBAL_ENTRIES) {
                            new_capacity = ONE_G02_GLOBAL_ENTRIES;
                        }
                        one_g02_index_entry *grown = (one_g02_index_entry *)realloc(
                            global, new_capacity * sizeof(*global)
                        );
                        if (grown == NULL) goto allocation_failure;
                        global = grown;
                        global_capacity = new_capacity;
                    }
                    global[global_count].key = selected_value;
                    global[global_count].start = anchor_start;
                    global[global_count].used = 1;
                    global_count += 1;
                    if (global_count > out->global_peak_entries) out->global_peak_entries = global_count;
                }
            }
        }

        if (r + 1 == block_size) {
            const uint64_t first_future_query = (q + 4) * (uint64_t)block_size;
            if (total_states > first_future_query) {
                size_t i = block_size - 1;
                suffix_offsets[base + i] = (uint16_t)i;
                out->derived_state_reads += 1;
                while (i > 0) {
                    const size_t current = i - 1;
                    const uint16_t next_argmin = suffix_offsets[base + i];
                    const uint64_t current_value = block_values[base + current];
                    const uint64_t suffix_value = block_values[base + next_argmin];
                    if (current_value < suffix_value) {
                        suffix_offsets[base + current] = (uint16_t)current;
                    } else {
                        suffix_offsets[base + current] = next_argmin;
                    }
                    out->derived_state_reads += 2;
                    i = current;
                }
                suffix_block_number[slot] = q;
                out->suffix_blocks_built += 1;
            } else {
                suffix_block_number[slot] = UINT64_MAX;
                out->suffix_blocks_skipped_dead += 1;
            }
            block_min_value[slot] = prefix_value;
            block_min_position[slot] = prefix_position;
            block_number[slot] = q;
        }

        states_seen += 1;
        if (r + 1 == block_size) {
            r = 0;
            q += 1;
        } else {
            r += 1;
        }
    }

    out->final_state = state;
    out->reserved_state_bytes +=
        sizeof(local) + global_capacity * sizeof(*global);
    free(global);
    free(block_values);
    free(suffix_offsets);
    return 0;

bad_state:
    free(global);
    free(block_values);
    free(suffix_offsets);
    return -5;
bad_suffix:
    free(global);
    free(block_values);
    free(suffix_offsets);
    return -6;
emit_failure:
    free(global);
    free(block_values);
    free(suffix_offsets);
    return -4;
allocation_failure:
    free(global);
    free(block_values);
    free(suffix_offsets);
    return -2;
}
