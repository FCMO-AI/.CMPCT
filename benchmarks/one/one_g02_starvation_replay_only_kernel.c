#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/* ONE-G0.2 causal decomposition arm.
 * Maintains the same starvation observation and 4,096-byte bounded history as the
 * byte-history rescue, and performs the exact Gear-state replay whenever rescue activates.
 * It deliberately does NOT build/maintain the rightmost-min queue or emit nominations.
 * Thus observation -> replay-only prices replay arithmetic; replay-only -> full rescue
 * prices queue construction/maintenance plus nomination bookkeeping.
 */

typedef struct {
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t sparse_anchors;
    uint64_t rescue_active_positions;
    uint64_t activation_events;
    uint64_t replayed_history_bytes;
    uint64_t replay_checksum;
    uint64_t reserved_state_bytes;
} one_g02_starvation_replay_only_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)

int one_g02_starvation_replay_only_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t span,
    one_g02_starvation_replay_only_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || span == 0) return -1;
    *out = (one_g02_starvation_replay_only_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    uint8_t *history = (uint8_t *)malloc(span);
    if (history == NULL) return -2;
    out->reserved_state_bytes = (uint64_t)span + (uint64_t)(256 * sizeof(uint64_t));

    size_t history_count = 0;
    size_t history_next = 0;
    uint64_t history_seed = 0;
    uint64_t state = 0;
    uint64_t last_sparse_position = UINT64_MAX;
    int active = 0;
    uint8_t run_value = data[0];
    size_t run_length = 0;

    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (run_length == 0) {
            run_value = value;
            run_length = 1;
        } else if (value == run_value) {
            run_length += 1;
        } else {
            run_value = value;
            run_length = 1;
        }

        uint64_t before = state;
        state = (state << 1) + gear[value];
        if (position + 1 < window) continue;
        out->positions_considered += 1;

        if (history_count == 0) {
            history_seed = before;
        } else if (history_count == span) {
            uint8_t oldest = history[history_next];
            history_seed = (history_seed << 1) + gear[oldest];
        }
        history[history_next] = value;
        history_next = (history_next + 1) % span;
        if (history_count < span) history_count += 1;

        int run_dominated = run_length >= (window > ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
        int sparse_anchor = ((state & ONE_G02_ANCHOR_MASK) == 0) && !run_dominated;
        if (sparse_anchor) {
            out->sparse_anchors += 1;
            last_sparse_position = (uint64_t)position;
            active = 0;
            continue;
        }

        uint64_t gap = last_sparse_position == UINT64_MAX
            ? (uint64_t)(position + 1 - window)
            : (uint64_t)position - last_sparse_position;
        if (run_dominated || gap < (uint64_t)span) continue;

        out->rescue_active_positions += 1;
        if (!active) {
            if (history_count < span) continue;
            uint64_t replay_state = history_seed;
            size_t oldest_slot = history_next;
            for (size_t j = 0; j < history_count; ++j) {
                uint8_t replay_value = history[(oldest_slot + j) % span];
                replay_state = (replay_state << 1) + gear[replay_value];
            }
            out->replayed_history_bytes += history_count;
            out->replay_checksum ^= replay_state;
            out->activation_events += 1;
            if (replay_state != state) {
                free(history);
                return -3;
            }
            active = 1;
        }
    }

    out->final_state = state;
    free(history);
    return 0;
}
