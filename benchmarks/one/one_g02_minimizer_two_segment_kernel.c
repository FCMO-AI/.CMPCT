#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 causal diagnostic: exact rightmost 4096-state sliding minimum using two
 * half-span segments.  This is a structural simplification of the frozen rejected
 * four-segment Builder, not a different selector: old partial suffix + one complete
 * middle block + current prefix still exactly partitions every mature window.
 *
 * Source bytes are consumed once.  The reader and ONE wire format are unaffected.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
} one_g02_two_segment_result;

static int emit_anchor(
    one_g02_two_segment_result *out,
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

int one_g02_minimizer_two_segment_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_two_segment_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 2 != 0) return -3;
    const size_t block_size = minimizer_span / 2;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;

    out->emitted = 0;
    out->final_state = 0;
    out->positions_considered = 0;
    out->reserved_state_bytes = 0;
    out->derived_state_reads = 0;
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    uint64_t *current_values = NULL;
    uint64_t *suffix_values = NULL;
    uint16_t *suffix_offsets = NULL;
    if (enabled) {
        current_values = (uint64_t *)malloc(block_size * sizeof(uint64_t));
        suffix_values = (uint64_t *)malloc(2 * block_size * sizeof(uint64_t));
        suffix_offsets = (uint16_t *)malloc(2 * block_size * sizeof(uint16_t));
        if (current_values == NULL || suffix_values == NULL || suffix_offsets == NULL) {
            free(current_values);
            free(suffix_values);
            free(suffix_offsets);
            return -2;
        }
        out->reserved_state_bytes =
            block_size * sizeof(uint64_t) +
            2 * block_size * (sizeof(uint64_t) + sizeof(uint16_t)) +
            2 * (sizeof(uint64_t) + sizeof(uint64_t) + sizeof(uint64_t));
    }

    uint64_t block_min_value[2] = {0, 0};
    uint64_t block_min_position[2] = {0, 0};
    uint64_t block_number[2] = {UINT64_MAX, UINT64_MAX};

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
            if (q >= 1) {
                const uint64_t b = q - 1;
                const size_t slot = (size_t)(b & 1u);
                if (block_number[slot] != b) return -5;
                middle_value = block_min_value[slot];
                middle_position = block_min_position[slot];
            }
        } else if (state <= prefix_value) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
        }
        current_values[r] = state;

        if (state_index + 1 >= minimizer_span) {
            uint64_t selected_value = middle_value;
            uint64_t selected_position = middle_position;
            /* middle is earlier than current prefix, so equality chooses the prefix. */
            if (prefix_value <= selected_value) {
                selected_value = prefix_value;
                selected_position = prefix_position;
            }

            /* The old partial suffix is earlier than both other candidates.  Strict less-than
             * is therefore required to preserve rightmost tie semantics. */
            if (q >= 2 && r + 1 < block_size) {
                const uint64_t old_block = q - 2;
                const size_t slot = (size_t)(old_block & 1u);
                if (block_number[slot] != old_block) return -5;
                const size_t idx = slot * block_size + r + 1;
                const uint64_t old_value = suffix_values[idx];
                if (old_value < selected_value) {
                    selected_value = old_value;
                    selected_position =
                        (uint64_t)(window - 1) + old_block * block_size + suffix_offsets[idx];
                }
            }

            int rc = emit_anchor(out, selected_position, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(current_values);
                free(suffix_values);
                free(suffix_offsets);
                return rc;
            }
        }

        if (r + 1 == block_size) {
            /* q-2's suffix is empty at this final offset, so its two-slot ring may be reused. */
            const size_t slot = (size_t)(q & 1u);
            const size_t base = slot * block_size;
            size_t i = block_size - 1;
            suffix_values[base + i] = current_values[i];
            suffix_offsets[base + i] = (uint16_t)i;
            out->derived_state_reads += 1;
            while (i > 0) {
                const size_t current = i - 1;
                const uint64_t value = current_values[current];
                if (value < suffix_values[base + i]) {
                    suffix_values[base + current] = value;
                    suffix_offsets[base + current] = (uint16_t)current;
                } else {
                    suffix_values[base + current] = suffix_values[base + i];
                    suffix_offsets[base + current] = suffix_offsets[base + i];
                }
                out->derived_state_reads += 1;
                i = current;
            }
            block_min_value[slot] = prefix_value;
            block_min_position[slot] = prefix_position;
            block_number[slot] = q;
        }

        state_index += 1;
    }

    out->final_state = state;
    free(current_values);
    free(suffix_values);
    free(suffix_offsets);
    return 0;
}
