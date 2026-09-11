#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 causal Builder: offset-only four-segment state with the running
 * suffix minimum retained in scalar registers during the backward build.
 *
 * The prior offset-only Builder removes the duplicated uint64 suffix-value
 * array, but then rereads block_values[next_argmin] on every backward step.
 * That exports roughly two derived-state reads per suffix element.  The suffix
 * recurrence already carries the minimum value and argmin from i+1 to i, so
 * keep both as scalars and write only the uint16 argmin table.  Query-time
 * semantics remain one offset load plus one retained-state value load.
 *
 * No selector, Gear identity, source pass, state budget, Law or reader surface
 * changes.  This isolates redundant derived-state read traffic.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads;
} one_g02_offset_cached_result;

static int emit_anchor(
    one_g02_offset_cached_result *out,
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

int one_g02_minimizer_offset_cached_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_offset_cached_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;

    *out = (one_g02_offset_cached_result){0};
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

    uint64_t block_min_value[4] = {0, 0, 0, 0};
    uint64_t block_min_position[4] = {0, 0, 0, 0};
    uint64_t block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    uint64_t suffix_block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};

    uint64_t state = 0;
    uint64_t prefix_value = 0;
    uint64_t prefix_position = 0;
    uint64_t middle_value = 0;
    uint64_t middle_position = 0;
    uint64_t last_emitted = UINT64_MAX;
    uint64_t states_seen = 0;
    uint64_t q = 0;
    size_t r = 0;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) continue;

        const size_t slot = (size_t)(q & 3u);
        const size_t base = slot * block_size;
        if (r == 0) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
            if (q >= 3) {
                uint64_t b = q - 3;
                size_t middle_slot = (size_t)(b & 3u);
                if (block_number[middle_slot] != b) return -5;
                middle_value = block_min_value[middle_slot];
                middle_position = block_min_position[middle_slot];
                for (b = q - 2; b <= q - 1; ++b) {
                    middle_slot = (size_t)(b & 3u);
                    if (block_number[middle_slot] != b) return -5;
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
                if (suffix_block_number[old_slot] != old_block) return -6;
                const size_t old_base = old_slot * block_size;
                const size_t idx = old_base + r + 1;
                const uint16_t argmin = suffix_offsets[idx];
                const uint64_t old_value = block_values[old_base + argmin];
                out->suffix_value_indirect_loads += 1;
                if (old_value < selected_value) {
                    selected_value = old_value;
                    selected_position =
                        (uint64_t)(window - 1) + old_block * block_size + argmin;
                }
            }
            const int rc = emit_anchor(out, selected_position, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(block_values);
                free(suffix_offsets);
                return rc;
            }
        }

        if (r + 1 == block_size) {
            const uint64_t first_future_query = (q + 4) * (uint64_t)block_size;
            if (total_states > first_future_query) {
                size_t i = block_size - 1;
                uint64_t suffix_value = block_values[base + i];
                uint16_t suffix_argmin = (uint16_t)i;
                suffix_offsets[base + i] = suffix_argmin;
                out->derived_state_reads += 1;
                while (i > 0) {
                    const size_t current = i - 1;
                    const uint64_t value = block_values[base + current];
                    if (value < suffix_value) {
                        suffix_value = value;
                        suffix_argmin = (uint16_t)current;
                    }
                    suffix_offsets[base + current] = suffix_argmin;
                    out->derived_state_reads += 1;
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
    free(block_values);
    free(suffix_offsets);
    return 0;
}
