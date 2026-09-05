#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 causal Builder: preserve the promoted tail-aware dense suffix tables,
 * but do not reload/reselect candidates on every mature window.
 *
 * The dense suffix table already stores the rightmost argmin offset. Once loaded,
 * that suffix candidate remains exact until the advancing window start passes its
 * argmin. Prefix minima change only on a new <= minimum; complete middle blocks are
 * constant for the whole current block. Therefore selection/emit work is needed only
 * at those events (plus first maturity and suffix disappearance), not at every byte.
 * This changes encoder maintenance scheduling only; Gear and selector semantics do not.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t mature_windows;
    uint64_t suffix_candidate_loads;
    uint64_t selection_recomputes;
    uint64_t prefix_change_events;
    uint64_t suffix_change_events;
} one_g02_event_result;

static int emit_anchor(
    one_g02_event_result *out,
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

int one_g02_minimizer_event_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_event_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;

    *out = (one_g02_event_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    const uint64_t total_states = length >= window ? (uint64_t)(length - window + 1) : 0;
    uint64_t *current_values = NULL;
    uint64_t *suffix_values = NULL;
    uint16_t *suffix_offsets = NULL;
    if (enabled) {
        current_values = (uint64_t *)malloc(block_size * sizeof(uint64_t));
        suffix_values = (uint64_t *)malloc(4 * block_size * sizeof(uint64_t));
        suffix_offsets = (uint16_t *)malloc(4 * block_size * sizeof(uint16_t));
        if (current_values == NULL || suffix_values == NULL || suffix_offsets == NULL) {
            free(current_values);
            free(suffix_values);
            free(suffix_offsets);
            return -2;
        }
        /* Same dense arrays as the promoted tail-aware baseline. */
        out->reserved_state_bytes =
            block_size * sizeof(uint64_t) +
            4 * block_size * (sizeof(uint64_t) + sizeof(uint16_t)) +
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
    uint64_t suffix_value = 0;
    uint64_t suffix_position = 0;
    uint16_t suffix_argmin = 0;
    int suffix_valid = 0;
    uint64_t selected_position = 0;
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
        int candidate_changed = 0;

        if (r == 0) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
            suffix_valid = 0;
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
            if (q >= 4) {
                const uint64_t old_block = q - 4;
                const size_t slot = (size_t)(old_block & 3u);
                if (suffix_block_number[slot] != old_block) return -6;
                const size_t idx = slot * block_size + 1;
                suffix_value = suffix_values[idx];
                suffix_argmin = suffix_offsets[idx];
                suffix_position =
                    (uint64_t)(window - 1) + old_block * block_size + suffix_argmin;
                suffix_valid = 1;
                out->suffix_candidate_loads += 1;
            }
            candidate_changed = 1;
        } else if (state <= prefix_value) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
            candidate_changed = 1;
            out->prefix_change_events += 1;
        }
        current_values[r] = state;

        if (state_index + 1 >= minimizer_span) {
            out->mature_windows += 1;

            if (q >= 4 && suffix_valid) {
                if (r + 1 >= block_size) {
                    suffix_valid = 0;
                    candidate_changed = 1;
                    out->suffix_change_events += 1;
                } else if (r + 1 > (size_t)suffix_argmin) {
                    const uint64_t old_block = q - 4;
                    const size_t slot = (size_t)(old_block & 3u);
                    const size_t idx = slot * block_size + r + 1;
                    suffix_value = suffix_values[idx];
                    suffix_argmin = suffix_offsets[idx];
                    suffix_position =
                        (uint64_t)(window - 1) + old_block * block_size + suffix_argmin;
                    candidate_changed = 1;
                    out->suffix_change_events += 1;
                    out->suffix_candidate_loads += 1;
                }
            }

            /* q=3,r=1023 is the first mature window; its candidates may have
             * evolved before maturity without prior selection work. */
            if (state_index + 1 == minimizer_span) candidate_changed = 1;

            if (candidate_changed) {
                uint64_t selected_value = middle_value;
                selected_position = middle_position;
                if (prefix_value <= selected_value) {
                    selected_value = prefix_value;
                    selected_position = prefix_position;
                }
                if (suffix_valid && suffix_value < selected_value) {
                    selected_position = suffix_position;
                }
                out->selection_recomputes += 1;

                int rc = emit_anchor(out, selected_position, trace, trace_capacity, &last_emitted);
                if (rc != 0) {
                    free(current_values);
                    free(suffix_values);
                    free(suffix_offsets);
                    return rc;
                }
            }
        }

        if (r + 1 == block_size) {
            const size_t slot = (size_t)(q & 3u);
            const uint64_t first_future_query = (q + 4) * (uint64_t)block_size;
            if (total_states > first_future_query) {
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

        state_index += 1;
    }

    out->final_state = state;
    free(current_values);
    free(suffix_values);
    free(suffix_offsets);
    return 0;
}
