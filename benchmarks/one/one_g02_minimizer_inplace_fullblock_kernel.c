#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 rehabilitation Builder: tail-aware in-place full-window prefix/suffix
 * maintenance for the exact 4096-state rightmost minimum.
 *
 * This revisits the previously rejected full-block family only after its startup
 * debt was causally identified as eager suffix work.  It also removes the old
 * duplicate raw-block + suffix-value arrays: while consuming the next block,
 * slot r of the outgoing suffix ring is dead before slot r+1 is queried, so the
 * new raw state can overwrite slot r in place.  When the block completes, the
 * same value ring is transformed backwards into rightmost suffix minima.
 *
 * Gear identity, window, tie semantics, anchor trace, source pass and reader
 * surface are unchanged.  This is encoder discovery only.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
} one_g02_inplace_fullblock_result;

static int emit_anchor(
    one_g02_inplace_fullblock_result *out,
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

int one_g02_minimizer_inplace_fullblock_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_inplace_fullblock_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span > UINT16_MAX) return -3;
    *out = (one_g02_inplace_fullblock_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    const uint64_t total_states = length >= window ? (uint64_t)(length - window + 1) : 0;
    uint64_t *values = NULL;
    uint16_t *suffix_offsets = NULL;
    if (enabled) {
        values = (uint64_t *)malloc(minimizer_span * sizeof(uint64_t));
        suffix_offsets = (uint16_t *)malloc(minimizer_span * sizeof(uint16_t));
        if (values == NULL || suffix_offsets == NULL) {
            free(values);
            free(suffix_offsets);
            return -2;
        }
        /* Heap state plus the three persistent u64 control scalars charged below. */
        out->reserved_state_bytes =
            minimizer_span * (sizeof(uint64_t) + sizeof(uint16_t)) +
            3 * sizeof(uint64_t);
    }

    uint64_t state = 0;
    uint64_t prefix_value = 0;
    uint64_t prefix_position = 0;
    uint64_t previous_block_base = 0;
    uint64_t last_emitted = UINT64_MAX;
    uint64_t q = 0;
    size_t r = 0;
    int have_previous_suffix = 0;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) continue;

        /* Query outgoing suffix r+1 before overwriting outgoing slot r. */
        uint64_t previous_value = 0;
        uint64_t previous_position = 0;
        int have_previous_candidate = 0;
        if (have_previous_suffix && r + 1 < minimizer_span) {
            previous_value = values[r + 1];
            previous_position = previous_block_base + suffix_offsets[r + 1];
            have_previous_candidate = 1;
        }

        values[r] = state;
        if (r == 0 || state <= prefix_value) {
            prefix_value = state;
            prefix_position = (uint64_t)position;
        }

        if (q > 0) {
            uint64_t anchor = prefix_position;
            if (have_previous_candidate && previous_value < prefix_value) {
                anchor = previous_position;
            }
            int rc = emit_anchor(out, anchor, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(values);
                free(suffix_offsets);
                return rc;
            }
        } else if (r + 1 == minimizer_span) {
            /* First mature window is exactly the first complete state block. */
            int rc = emit_anchor(out, prefix_position, trace, trace_capacity, &last_emitted);
            if (rc != 0) {
                free(values);
                free(suffix_offsets);
                return rc;
            }
        }

        if (r + 1 == minimizer_span) {
            /* A completed block q is queried only by states in q+1. If no such mature
             * query exists, the backward derived-state pass is dead and is skipped. */
            const uint64_t first_future_state = (q + 1) * (uint64_t)minimizer_span;
            if (total_states > first_future_state) {
                size_t i = minimizer_span - 1;
                suffix_offsets[i] = (uint16_t)i;
                out->derived_state_reads += 1;
                while (i > 0) {
                    const size_t current = i - 1;
                    const uint64_t value = values[current];
                    const uint64_t suffix_value = values[i];
                    if (value < suffix_value) {
                        suffix_offsets[current] = (uint16_t)current;
                    } else {
                        values[current] = suffix_value;
                        suffix_offsets[current] = suffix_offsets[i];
                    }
                    out->derived_state_reads += 1;
                    i = current;
                }
                previous_block_base =
                    (uint64_t)(position + 1 - minimizer_span);
                have_previous_suffix = 1;
                out->suffix_blocks_built += 1;
            } else {
                have_previous_suffix = 0;
                out->suffix_blocks_skipped_dead += 1;
            }
            r = 0;
            q += 1;
        } else {
            r += 1;
        }
    }

    out->final_state = state;
    free(values);
    free(suffix_offsets);
    return 0;
}
