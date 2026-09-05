#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 hostile performance A/B arm.
 *
 * Semantics intentionally match the canonical rightmost rolling-minimum selector. This arm
 * tests whether residual ring-addressing work is still a material owner after branch-wrap by
 * exploiting the already-frozen 4096-position minimizer span as a power-of-two mask. It is
 * encoder discovery instrumentation only; no reader-visible representation changes.
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

int one_g02_minimizer_mask_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_min_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if ((minimizer_span & (minimizer_span - 1)) != 0) return -3;
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

    const size_t ring_mask = minimizer_span - 1;
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
            head = (head + 1) & ring_mask;
            count -= 1;
        }

        while (count > 0) {
            size_t tail_index = (head + count - 1) & ring_mask;
            if (queue[tail_index].value < state) break;
            count -= 1;
        }
        size_t insert_index = (head + count) & ring_mask;
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
