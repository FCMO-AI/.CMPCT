#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/* ONE-G0.2 encoder-discovery research kernel.
 *
 * Retains only a bounded byte history + Gear table and reconstructs the rightmost-minimum
 * candidate at starvation episode edges. There is no continuously maintained minimizer
 * queue. This is deliberately discovery-only; no reader semantics live here.
 */
typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t sparse_anchors;
    uint64_t pulses;
    uint64_t replayed_history_bytes;
    uint64_t reserved_state_bytes;
} one_g02_edge_pulse_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)

static int emit_pulse(
    const uint8_t *history, size_t history_count, size_t history_next, uint64_t history_seed,
    const uint64_t gear[256], size_t span, uint64_t history_last_position,
    one_g02_edge_pulse_result *out, uint64_t *trace, size_t trace_capacity,
    uint64_t *last_emitted_position
) {
    if (history_count < span) return 0;
    uint64_t replay = history_seed;
    uint64_t best = UINT64_MAX;
    uint64_t anchor = 0;
    uint64_t oldest_position = history_last_position + 1 - (uint64_t)history_count;
    size_t oldest_slot = history_next;
    for (size_t j = 0; j < history_count; ++j) {
        uint8_t value = history[(oldest_slot + j) % span];
        replay = (replay << 1) + gear[value];
        /* <= implements rightmost-min tie semantics. */
        if (replay <= best) {
            best = replay;
            anchor = oldest_position + (uint64_t)j;
        }
    }
    out->pulses += 1;
    out->replayed_history_bytes += history_count;
    if (anchor == *last_emitted_position) return 0;
    *last_emitted_position = anchor;
    if (trace != NULL) {
        if (out->emitted >= trace_capacity) return -4;
        trace[out->emitted] = anchor;
    }
    out->emitted += 1;
    return 0;
}

int one_g02_starvation_edge_pulse_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256], size_t window, size_t span,
    one_g02_edge_pulse_result *out, uint64_t *trace, size_t trace_capacity
) {
    if (!out || !gear || !window || !span) return -1;
    *out = (one_g02_edge_pulse_result){0};
    if (!length) return 0;
    if (!data) return -1;

    uint8_t *history = (uint8_t *)malloc(span);
    if (!history) return -2;
    out->reserved_state_bytes = (uint64_t)span + (uint64_t)(256 * sizeof(uint64_t));

    size_t history_count = 0, history_next = 0;
    uint64_t history_seed = 0, state = 0, last_sparse = UINT64_MAX;
    uint64_t last_emitted = UINT64_MAX;
    uint64_t history_last_position = 0;
    int active = 0;
    uint8_t run_value = data[0];
    size_t run_length = 0;

    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (!run_length) { run_value = value; run_length = 1; }
        else if (value == run_value) run_length++;
        else { run_value = value; run_length = 1; }

        uint64_t before = state;
        state = (state << 1) + gear[value];
        if (position + 1 < window) continue;
        out->positions_considered++;

        int run_dominated = run_length >= (window > ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
        int sparse = ((state & ONE_G02_ANCHOR_MASK) == 0) && !run_dominated;

        /* Semantic edge-pulse oracle closes an active episode using history before the
         * sparse reset, so pulse before appending the current sparse position. */
        if (sparse && active && history_count == span) {
            int rc = emit_pulse(history, history_count, history_next, history_seed, gear, span,
                                history_last_position, out, trace, trace_capacity, &last_emitted);
            if (rc) { free(history); return rc; }
            active = 0;
            last_emitted = UINT64_MAX;
        }

        if (history_count == 0) {
            history_seed = before;
        } else if (history_count == span) {
            uint8_t oldest = history[history_next];
            history_seed = (history_seed << 1) + gear[oldest];
        }
        history[history_next] = value;
        history_next = (history_next + 1) % span;
        if (history_count < span) history_count++;
        history_last_position = (uint64_t)position;

        if (sparse) {
            out->sparse_anchors++;
            last_sparse = (uint64_t)position;
            continue;
        }
        if (run_dominated) continue;

        uint64_t gap = last_sparse == UINT64_MAX
            ? (uint64_t)(position + 1 - window)
            : (uint64_t)position - last_sparse;
        if (gap >= (uint64_t)span && !active && history_count == span) {
            int rc = emit_pulse(history, history_count, history_next, history_seed, gear, span,
                                history_last_position, out, trace, trace_capacity, &last_emitted);
            if (rc) { free(history); return rc; }
            active = 1;
        }
    }

    if (active && history_count == span) {
        int rc = emit_pulse(history, history_count, history_next, history_seed, gear, span,
                            history_last_position, out, trace, trace_capacity, &last_emitted);
        if (rc) { free(history); return rc; }
    }
    out->final_state = state;
    free(history);
    return 0;
}
