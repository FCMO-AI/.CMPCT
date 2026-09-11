#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 hostile performance A/B arm.
 *
 * Semantics intentionally match one_g02_minimizer_kernel.c exactly. The sole mechanism
 * change is replacing runtime modulo in the bounded ring with branch/single-subtract wrap.
 * This remains encoder-discovery research, not reader/runtime surface.
 */

typedef struct {
    uint64_t emitted;
    uint64_t peak_queue;
    uint64_t final_state;
    uint64_t positions_considered;
} one_g02_min_result;

typedef struct {
    uint64_t value;
    uint64_t position;
} queue_entry;

static size_t wrap_once(size_t value, size_t span) {
    return value >= span ? value - span : value;
}

int one_g02_minimizer_branch_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_min_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span > SIZE_MAX - window) return -1;
    out->emitted = 0;
    out->peak_queue = 0;
    out->final_state = 0;
    out->positions_considered = 0;
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int minimizer_enabled = length >= minimizer_span + window;
    queue_entry *queue = NULL;
    if (minimizer_enabled) {
        queue = (queue_entry *)malloc(minimizer_span * sizeof(queue_entry));
        if (queue == NULL) return -2;
    }

    size_t head = 0;
    size_t count = 0;
    uint64_t state = 0;
    uint64_t last_emitted_position = UINT64_MAX;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!minimizer_enabled) continue;

        uint64_t first_valid = 0;
        if (position + 1 >= minimizer_span) {
            first_valid = (uint64_t)(position + 1 - minimizer_span);
        }
        while (count > 0 && queue[head].position < first_valid) {
            head += 1;
            if (head == minimizer_span) head = 0;
            count -= 1;
        }

        while (count > 0) {
            size_t tail_index = wrap_once(head + count - 1, minimizer_span);
            if (queue[tail_index].value < state) break;
            count -= 1;
        }
        size_t insert_index = wrap_once(head + count, minimizer_span);
        queue[insert_index].value = state;
        queue[insert_index].position = (uint64_t)position;
        count += 1;

        if (count > out->peak_queue) out->peak_queue = count;
        if (first_valid < window - 1 || count == 0) continue;
        uint64_t anchor_position = queue[head].position;
        if (anchor_position != last_emitted_position) {
            last_emitted_position = anchor_position;
            out->emitted += 1;
        }
    }

    out->final_state = state;
    free(queue);
    return 0;
}
