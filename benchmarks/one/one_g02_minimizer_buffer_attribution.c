#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/* Diagnostic-only ablations. They do not emit anchors and are not selector candidates. */
typedef struct {
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t checksum;
} one_g02_buffer_attr_result;

int one_g02_store_only_cost_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_buffer_attr_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    *out = (one_g02_buffer_attr_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;
    const int enabled = length >= minimizer_span + window;
    uint64_t *current_values = NULL;
    if (enabled) {
        current_values = (uint64_t *)malloc(block_size * sizeof(uint64_t));
        if (current_values == NULL) return -2;
        out->reserved_state_bytes = block_size * sizeof(uint64_t);
    }
    uint64_t state = 0, state_index = 0;
    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) { state_index += 1; continue; }
        const size_t r = (size_t)(state_index % block_size);
        current_values[r] = state;
        if (r + 1 == block_size) {
#if defined(__GNUC__) || defined(__clang__)
            __asm__ __volatile__("" : : "r"(current_values) : "memory");
#endif
            out->checksum ^= current_values[0] + current_values[block_size - 1];
        }
        state_index += 1;
    }
    out->final_state = state;
    free(current_values);
    return 0;
}

int one_g02_prefix_only_cost_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_buffer_attr_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    *out = (one_g02_buffer_attr_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;
    const int enabled = length >= minimizer_span + window;
    uint64_t state = 0, state_index = 0, prefix_value = 0, prefix_position = 0;
    uint64_t block_min_value[4] = {0,0,0,0};
    uint64_t block_min_position[4] = {0,0,0,0};
    if (enabled) out->reserved_state_bytes = 4 * 2 * sizeof(uint64_t);
    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) { state_index += 1; continue; }
        const uint64_t q = state_index / block_size;
        const size_t r = (size_t)(state_index % block_size);
        if (r == 0) { prefix_value = state; prefix_position = (uint64_t)position; }
        else if (state <= prefix_value) { prefix_value = state; prefix_position = (uint64_t)position; }
        if (r + 1 == block_size) {
            const size_t slot = (size_t)(q & 3u);
            block_min_value[slot] = prefix_value;
            block_min_position[slot] = prefix_position;
            out->checksum ^= block_min_value[slot] + block_min_position[slot];
        }
        state_index += 1;
    }
    out->final_state = state;
    return 0;
}
