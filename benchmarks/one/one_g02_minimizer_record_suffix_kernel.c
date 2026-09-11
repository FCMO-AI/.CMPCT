#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 causal Builder: exact four-segment rightmost minimum with tail-aware
 * suffix construction represented as strict record-minimum change points.
 *
 * Dense segmented maintenance stores one suffix-minimum (value, offset) for every
 * derived state.  The suffix-minimum function changes only when a strict new record
 * minimum appears while scanning a block right-to-left.  Future queries advance in
 * increasing start-offset order, so one monotone cursor consumes those change points
 * without search or source-byte rescans. Worst-case allocation remains bounded to one
 * record per block state; this changes maintenance representation, not selector semantics.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_record_writes;
    uint64_t suffix_record_advances;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t max_records_per_block;
} one_g02_record_suffix_result;

static int emit_anchor(
    one_g02_record_suffix_result *out,
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
    return 0;
}

int one_g02_minimizer_record_suffix_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_record_suffix_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;

    *out = (one_g02_record_suffix_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    const uint64_t total_states = length >= window ? (uint64_t)(length - window + 1) : 0;
    uint64_t *current_values = NULL;
    uint64_t *record_values = NULL;
    uint16_t *record_starts = NULL;
    if (enabled) {
        current_values = (uint64_t *)malloc(block_size * sizeof(uint64_t));
        record_values = (uint64_t *)malloc(4 * block_size * sizeof(uint64_t));
        record_starts = (uint16_t *)malloc(4 * block_size * sizeof(uint16_t));
        if (current_values == NULL || record_values == NULL || record_starts == NULL) {
            free(current_values);
            free(record_values);
            free(record_starts);
            return -2;
        }
        /* Charge worst-case record capacity, not friendly observed occupancy. */
        out->reserved_state_bytes =
            block_size * sizeof(uint64_t) +
            4 * block_size * (sizeof(uint64_t) + sizeof(uint16_t)) +
            4 * 7 * sizeof(uint64_t);
    }

    uint64_t block_min_value[4] = {0, 0, 0, 0};
    uint64_t block_min_position[4] = {0, 0, 0, 0};
    uint64_t block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    uint64_t suffix_block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    size_t record_end[4] = {0, 0, 0, 0};
    size_t record_cursor[4] = {0, 0, 0, 0};

    uint64_t state = 0;
    uint64_t prefix_value = 0;
    uint64_t prefix_position = 0;
    uint64_t middle_value = 0;
    uint64_t middle_position = 0;
    uint64_t last_emitted = UINT64_MAX;
    uint64_t state_index = 0;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) {
            state_index += 1;
            continue;
        }

        const uint64_t q = state_index / block_size;
        const size_t r = (size_t)(state_index % block_size);
        if (r == 0) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
            if (q >= 3) {
                uint64_t b = q - 3;
                size_t slot = (size_t)(b & 3u);
                if (block_number[slot] != b) return -5;
                middle_value = block_min_value[slot];
                middle_position = block_min_position[slot];
                for (b = q - 2; b <= q - 1; ++b) {
                    slot = (size_t)(b & 3u);
                    if (block_number[slot] != b) return -5;
                    if (block_min_value[slot] <= middle_value) {
                        middle_value = block_min_value[slot];
                        middle_position = block_min_position[slot];
                    }
                }
            }
        } else if (state <= prefix_value) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
        }
        current_values[r] = state;

        if (state_index + 1 >= minimizer_span) {
            uint64_t selected_value = middle_value;
            uint64_t selected_position = middle_position;
            if (prefix_value <= selected_value) {
                selected_value = prefix_value;
                selected_position = prefix_position;
            }

            if (q >= 4 && r + 1 < block_size) {
                const uint64_t old_block = q - 4;
                const size_t slot = (size_t)(old_block & 3u);
                if (suffix_block_number[slot] != old_block) return -6;
                size_t cursor = record_cursor[slot];
                const size_t end = record_end[slot];
                const uint16_t wanted = (uint16_t)(r + 1);
                while (
                    cursor < end &&
                    record_starts[slot * block_size + cursor] < wanted
                ) {
                    cursor += 1;
                    out->suffix_record_advances += 1;
                }
                if (cursor >= end) return -7;
                record_cursor[slot] = cursor;
                const size_t idx = slot * block_size + cursor;
                const uint64_t old_value = record_values[idx];
                if (old_value < selected_value) {
                    selected_value = old_value;
                    selected_position =
                        (uint64_t)(window - 1) + old_block * block_size + record_starts[idx];
                }
            }

            int rc = emit_anchor(out, selected_position, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(current_values);
                free(record_values);
                free(record_starts);
                return rc;
            }
        }

        if (r + 1 == block_size) {
            const size_t slot = (size_t)(q & 3u);
            const uint64_t first_future_query = (q + 4) * (uint64_t)block_size;
            if (total_states > first_future_query) {
                const size_t base = slot * block_size;
                size_t write = block_size;
                size_t i = block_size - 1;
                uint64_t min_value = current_values[i];

                write -= 1;
                record_values[base + write] = min_value;
                record_starts[base + write] = (uint16_t)i;
                out->derived_state_reads += 1;
                out->suffix_record_writes += 1;

                while (i > 0) {
                    const size_t current = i - 1;
                    const uint64_t value = current_values[current];
                    out->derived_state_reads += 1;
                    /* Strict less-than preserves the rightmost tie already to our right. */
                    if (value < min_value) {
                        min_value = value;
                        write -= 1;
                        record_values[base + write] = value;
                        record_starts[base + write] = (uint16_t)current;
                        out->suffix_record_writes += 1;
                    }
                    i = current;
                }

                record_end[slot] = block_size;
                record_cursor[slot] = write;
                suffix_block_number[slot] = q;
                out->suffix_blocks_built += 1;
                const uint64_t records = (uint64_t)(block_size - write);
                if (records > out->max_records_per_block) {
                    out->max_records_per_block = records;
                }
            } else {
                suffix_block_number[slot] = UINT64_MAX;
                record_end[slot] = 0;
                record_cursor[slot] = 0;
                out->suffix_blocks_skipped_dead += 1;
            }
            block_min_value[slot] = prefix_value;
            block_min_position[slot] = prefix_position;
            block_number[slot] = q;
        }

        state_index += 1;
    }

    out->final_state = state;
    free(current_values);
    free(record_values);
    free(record_starts);
    return 0;
}
