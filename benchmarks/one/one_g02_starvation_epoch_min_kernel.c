#include <stddef.h>
#include <stdint.h>

/* ONE-G0.2 encoder-discovery research kernel.
 *
 * Maintains one scalar rightmost-minimum over consecutive starvation epochs. There is no
 * sliding minimizer queue, raw-history buffer, block hierarchy, or replay. The candidate is
 * deliberately allowed to nominate a different subset from the mature minimizer; transfer
 * evidence, not opcode identity, decides whether the simpler discovery sufficient statistic
 * survives.
 */
typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t sparse_anchors;
    uint64_t pulses;
    uint64_t reserved_state_bytes;
} one_g02_epoch_min_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)

static int emit_epoch(
    uint64_t min_position,
    one_g02_epoch_min_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (min_position == UINT64_MAX) return 0;
    if (trace != NULL) {
        if (out->emitted >= trace_capacity) return -4;
        trace[out->emitted] = min_position;
    }
    out->emitted += 1;
    out->pulses += 1;
    return 0;
}

int one_g02_starvation_epoch_min_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t span,
    one_g02_epoch_min_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || span == 0) return -1;
    *out = (one_g02_epoch_min_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    /* Charge the Gear table plus the persistent scalar discovery state. */
    out->reserved_state_bytes = (uint64_t)(256 * sizeof(uint64_t)) + (uint64_t)(5 * sizeof(uint64_t));

    uint64_t state = 0;
    uint64_t last_sparse_position = UINT64_MAX;
    uint64_t min_signal = UINT64_MAX;
    uint64_t min_position = UINT64_MAX;
    uint64_t epoch_count = 0;
    int active = 0;
    uint8_t run_value = data[0];
    size_t run_length = 0;

    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (run_length == 0) { run_value = value; run_length = 1; }
        else if (value == run_value) { run_length += 1; }
        else { run_value = value; run_length = 1; }

        state = (state << 1) + gear[value];
        if (position + 1 < window) continue;
        out->positions_considered += 1;

        int run_dominated = run_length >= (window > ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
        int sparse_anchor = ((state & ONE_G02_ANCHOR_MASK) == 0) && !run_dominated;
        if (sparse_anchor) {
            if (active) {
                int rc = emit_epoch(min_position, out, trace, trace_capacity);
                if (rc) return rc;
            }
            out->sparse_anchors += 1;
            last_sparse_position = (uint64_t)position;
            active = 0;
            min_signal = UINT64_MAX;
            min_position = UINT64_MAX;
            epoch_count = 0;
            continue;
        }
        if (run_dominated) continue;

        epoch_count += 1;
        if (state <= min_signal) {
            min_signal = state;
            min_position = (uint64_t)position;
        }

        uint64_t gap = last_sparse_position == UINT64_MAX
            ? (uint64_t)(position + 1 - window)
            : (uint64_t)position - last_sparse_position;
        if (!active && gap >= (uint64_t)span) {
            int rc = emit_epoch(min_position, out, trace, trace_capacity);
            if (rc) return rc;
            min_signal = UINT64_MAX;
            min_position = UINT64_MAX;
            epoch_count = 0;
            active = 1;
        } else if (active && epoch_count >= (uint64_t)span) {
            int rc = emit_epoch(min_position, out, trace, trace_capacity);
            if (rc) return rc;
            min_signal = UINT64_MAX;
            min_position = UINT64_MAX;
            epoch_count = 0;
        }
    }

    if (active) {
        int rc = emit_epoch(min_position, out, trace, trace_capacity);
        if (rc) return rc;
    }
    out->final_state = state;
    return 0;
}
