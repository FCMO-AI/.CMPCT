#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * ONE-G0.2 diagnostic ablation kernels.
 *
 * These are NOT selector candidates: they deliberately omit anchor emission so that
 * elapsed cost can be attributed across maintenance layers.  The compiler barrier at
 * block completion makes the derived dense tables observably materialized and prevents
 * dead-store elimination from gifting away the memory work being measured.
 */

typedef struct {
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t checksum;
} one_g02_cost_result;

static inline void preserve_dense_tables(uint64_t *values, uint16_t *offsets) {
#if defined(__GNUC__) || defined(__clang__)
    __asm__ __volatile__("" : : "r"(values), "r"(offsets) : "memory");
#else
    volatile uint64_t sink = values[0] ^ (uint64_t)offsets[0];
    (void)sink;
#endif
}

int one_g02_buffer_prefix_cost_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_cost_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0) return -3;
    *out = (one_g02_cost_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    uint64_t *current_values = NULL;
    if (enabled) {
        current_values = (uint64_t *)malloc(block_size * sizeof(uint64_t));
        if (current_values == NULL) return -2;
        out->reserved_state_bytes = block_size * sizeof(uint64_t) + 4 * 3 * sizeof(uint64_t);
    }

    uint64_t block_min_value[4] = {0, 0, 0, 0};
    uint64_t block_min_position[4] = {0, 0, 0, 0};
    uint64_t block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    uint64_t state = 0, prefix_value = 0, prefix_position = 0, state_index = 0;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) { state_index += 1; continue; }

        const uint64_t q = state_index / block_size;
        const size_t r = (size_t)(state_index % block_size);
        if (r == 0) { prefix_value = state; prefix_position = (uint64_t)position; }
        else if (state <= prefix_value) { prefix_value = state; prefix_position = (uint64_t)position; }
        current_values[r] = state;

        if (r + 1 == block_size) {
            const size_t slot = (size_t)(q & 3u);
            block_min_value[slot] = prefix_value;
            block_min_position[slot] = prefix_position;
            block_number[slot] = q;
            out->checksum ^= block_min_value[slot] + block_min_position[slot] + block_number[slot];
#if defined(__GNUC__) || defined(__clang__)
            __asm__ __volatile__("" : : "r"(current_values) : "memory");
#endif
        }
        state_index += 1;
    }
    out->final_state = state;
    free(current_values);
    return 0;
}

int one_g02_dense_suffix_cost_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_cost_result *out
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;
    *out = (one_g02_cost_result){0};
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
            free(current_values); free(suffix_values); free(suffix_offsets); return -2;
        }
        out->reserved_state_bytes =
            block_size * sizeof(uint64_t) +
            4 * block_size * (sizeof(uint64_t) + sizeof(uint16_t)) +
            4 * 3 * sizeof(uint64_t);
    }

    uint64_t block_min_value[4] = {0, 0, 0, 0};
    uint64_t block_min_position[4] = {0, 0, 0, 0};
    uint64_t block_number[4] = {UINT64_MAX, UINT64_MAX, UINT64_MAX, UINT64_MAX};
    uint64_t state = 0, prefix_value = 0, prefix_position = 0, state_index = 0;

    for (size_t position = 0; position < length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) { state_index += 1; continue; }

        const uint64_t q = state_index / block_size;
        const size_t r = (size_t)(state_index % block_size);
        if (r == 0) { prefix_value = state; prefix_position = (uint64_t)position; }
        else if (state <= prefix_value) { prefix_value = state; prefix_position = (uint64_t)position; }
        current_values[r] = state;

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
                preserve_dense_tables(suffix_values + base, suffix_offsets + base);
                out->checksum ^= suffix_values[base] + (uint64_t)suffix_offsets[base];
                out->suffix_blocks_built += 1;
            } else {
                out->suffix_blocks_skipped_dead += 1;
            }
            block_min_value[slot] = prefix_value;
            block_min_position[slot] = prefix_position;
            block_number[slot] = q;
            out->checksum ^= block_min_value[slot] + block_min_position[slot] + block_number[slot];
        }
        state_index += 1;
    }

    out->final_state = state;
    free(current_values); free(suffix_values); free(suffix_offsets);
    return 0;
}
