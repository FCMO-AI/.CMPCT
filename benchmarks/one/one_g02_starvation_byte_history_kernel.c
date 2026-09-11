#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 research-only encoder-discovery microkernel.
 *
 * This ports the already-exact 4,096-position sparse-anchor starvation gate plus bounded
 * byte-history replay into compiled code. It emits selector nominations only; exact proof,
 * extension, reuse indexing and Law construction remain outside this kernel. It therefore
 * cannot be used as product-speed or stored-byte authority.
 */

typedef struct {
    uint64_t value;
    uint64_t position;
} one_g02_starvation_queue_entry;

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t sparse_anchors;
    uint64_t rescue_active_positions;
    uint64_t replayed_history_bytes;
    uint64_t peak_queue_entries;
    uint64_t reserved_state_bytes;
} one_g02_starvation_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)

static void queue_push_rightmost_min(
    one_g02_starvation_queue_entry *queue,
    size_t span,
    size_t *head,
    size_t *count,
    uint64_t signal,
    uint64_t position
) {
    while (*count > 0) {
        size_t tail = (*head + *count - 1) % span;
        if (queue[tail].value < signal) break;
        *count -= 1;
    }
    size_t insert = (*head + *count) % span;
    queue[insert].value = signal;
    queue[insert].position = position;
    *count += 1;
}

int one_g02_starvation_byte_history_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t span,
    one_g02_starvation_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || span == 0) return -1;
    *out = (one_g02_starvation_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    uint8_t *history = (uint8_t *)malloc(span);
    one_g02_starvation_queue_entry *queue =
        (one_g02_starvation_queue_entry *)malloc(span * sizeof(*queue));
    if (history == NULL || queue == NULL) {
        free(history);
        free(queue);
        return -2;
    }
    out->reserved_state_bytes =
        (uint64_t)span + (uint64_t)(span * sizeof(*queue)) + (uint64_t)(256 * sizeof(uint64_t));

    size_t history_count = 0;
    size_t history_next = 0;
    uint64_t history_seed = 0;
    size_t head = 0;
    size_t count = 0;
    int active = 0;
    uint64_t state = 0;
    uint64_t last_sparse_position = UINT64_MAX;
    uint64_t last_emitted_position = UINT64_MAX;
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
            head = 0;
            count = 0;
            last_emitted_position = UINT64_MAX;
            continue;
        }

        uint64_t gap = last_sparse_position == UINT64_MAX
            ? (uint64_t)(position + 1 - window)
            : (uint64_t)position - last_sparse_position;
        if (run_dominated || gap < (uint64_t)span) continue;

        out->rescue_active_positions += 1;
        if (!active) {
            if (history_count < span) continue;
            head = 0;
            count = 0;
            uint64_t replay_state = history_seed;
            uint64_t oldest_position = (uint64_t)(position + 1 - history_count);
            size_t oldest_slot = history_next;
            for (size_t j = 0; j < history_count; ++j) {
                uint8_t replay_value = history[(oldest_slot + j) % span];
                replay_state = (replay_state << 1) + gear[replay_value];
                queue_push_rightmost_min(
                    queue, span, &head, &count, replay_state, oldest_position + (uint64_t)j
                );
            }
            out->replayed_history_bytes += history_count;
            if (replay_state != state) {
                free(history);
                free(queue);
                return -3;
            }
            active = 1;
        } else {
            uint64_t first_valid = (uint64_t)(position + 1 - span);
            while (count > 0 && queue[head].position < first_valid) {
                head = (head + 1) % span;
                count -= 1;
            }
            queue_push_rightmost_min(queue, span, &head, &count, state, (uint64_t)position);
        }

        if (count > out->peak_queue_entries) out->peak_queue_entries = count;
        if (count == 0) continue;
        uint64_t anchor_position = queue[head].position;
        if (anchor_position == last_emitted_position) continue;
        last_emitted_position = anchor_position;
        if (trace != NULL) {
            if (out->emitted >= trace_capacity) {
                free(history);
                free(queue);
                return -4;
            }
            trace[out->emitted] = anchor_position;
        }
        out->emitted += 1;
    }

    out->final_state = state;
    free(history);
    free(queue);
    return 0;
}
