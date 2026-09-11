#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 causal Builder: exact rightmost sliding minimum via block prefix/suffix state.
 *
 * This changes encoder-side maintenance only. Gear identity, span, rightmost tie semantics,
 * emitted anchor positions and reader-visible representation are unchanged. The algorithm
 * consumes source bytes once. Its extra backward pass touches derived Gear-state values only.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
} one_g02_block_result;

static int emit_anchor(
    one_g02_block_result *out,
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

int one_g02_minimizer_block_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_block_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span > UINT16_MAX) return -3;
    out->emitted = 0;
    out->final_state = 0;
    out->positions_considered = 0;
    out->reserved_state_bytes = 0;
    out->derived_state_reads = 0;
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    uint64_t *block_values = NULL;
    uint64_t *suffix_values = NULL;
    uint16_t *suffix_offsets = NULL;
    if (enabled) {
        block_values = (uint64_t *)malloc(minimizer_span * sizeof(uint64_t));
        suffix_values = (uint64_t *)malloc(minimizer_span * sizeof(uint64_t));
        suffix_offsets = (uint16_t *)malloc(minimizer_span * sizeof(uint16_t));
        if (block_values == NULL || suffix_values == NULL || suffix_offsets == NULL) {
            free(block_values);
            free(suffix_values);
            free(suffix_offsets);
            return -2;
        }
        out->reserved_state_bytes = minimizer_span *
            (sizeof(uint64_t) + sizeof(uint64_t) + sizeof(uint16_t));
    }

    uint64_t state = 0;
    uint64_t prefix_value = 0;
    uint64_t prefix_position = 0;
    uint64_t previous_block_base = 0;
    uint64_t last_emitted = UINT64_MAX;
    size_t block_offset = 0;
    int have_previous_block = 0;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) continue;

        block_values[block_offset] = state;
        if (block_offset == 0 || state <= prefix_value) {
            /* <= makes equal minima choose the rightmost/current position. */
            prefix_value = state;
            prefix_position = (uint64_t)position;
        }

        if (have_previous_block) {
            uint64_t anchor;
            if (block_offset + 1 < minimizer_span) {
                const uint64_t previous_value = suffix_values[block_offset + 1];
                const uint64_t previous_position = previous_block_base + suffix_offsets[block_offset + 1];
                /* Current block is later, so equality must choose its rightmost prefix min. */
                anchor = (prefix_value <= previous_value) ? prefix_position : previous_position;
            } else {
                anchor = prefix_position;
            }
            int rc = emit_anchor(out, anchor, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(block_values);
                free(suffix_values);
                free(suffix_offsets);
                return rc;
            }
        } else if (block_offset + 1 == minimizer_span) {
            /* First mature window is exactly the first complete state block. */
            int rc = emit_anchor(out, prefix_position, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(block_values);
                free(suffix_values);
                free(suffix_offsets);
                return rc;
            }
        }

        block_offset += 1;
        if (block_offset == minimizer_span) {
            /* Build rightmost suffix minima for the next block. This is a derived-state pass,
             * not a second source-byte scan. Equal values keep the later suffix position. */
            size_t i = minimizer_span - 1;
            suffix_values[i] = block_values[i];
            suffix_offsets[i] = (uint16_t)i;
            out->derived_state_reads += 1;
            while (i > 0) {
                const size_t current = i - 1;
                const uint64_t value = block_values[current];
                if (value < suffix_values[i]) {
                    suffix_values[current] = value;
                    suffix_offsets[current] = (uint16_t)current;
                } else {
                    suffix_values[current] = suffix_values[i];
                    suffix_offsets[current] = suffix_offsets[i];
                }
                out->derived_state_reads += 1;
                i = current;
            }
            previous_block_base = (uint64_t)(position + 1 - minimizer_span);
            have_previous_block = 1;
            block_offset = 0;
        }
    }

    out->final_state = state;
    free(block_values);
    free(suffix_values);
    free(suffix_offsets);
    return 0;
}
