#include <stddef.h>
#include <stdint.h>

/*
 * ONE-G0.2 rehabilitation of the rejected 8 KiB dispatcher.
 *
 * The first Builder copied the selected selector's result struct field by
 * field after an extra call.  This version relies only on the already-common
 * result prefix ABI, zeroes the larger result once, writes the path bit, and
 * returns the selected selector call directly.  The 8192-byte opportunity
 * boundary is unchanged from the frozen crossover evidence.
 *
 * This is encoder-discovery integration only; selector semantics, Gear,
 * window/span, source pass, reader surface, Law and stored bytes do not change.
 */

#define ONE_G02_OFFSET_DISPATCH_BYTES ((size_t)8192)

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
} one_g02_segmented_counter_result;

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads;
} one_g02_offset_only_result;

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads;
    uint64_t selected_offset_path;
} one_g02_size_dispatch_tail_result;

int one_g02_minimizer_segmented_counter_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256],
    size_t window, size_t minimizer_span,
    one_g02_segmented_counter_result *out, uint64_t *trace,
    size_t trace_capacity
);

int one_g02_minimizer_offset_only_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256],
    size_t window, size_t minimizer_span,
    one_g02_offset_only_result *out, uint64_t *trace,
    size_t trace_capacity
);

int one_g02_minimizer_size_dispatch_tail_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_size_dispatch_tail_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL) return -1;
    *out = (one_g02_size_dispatch_tail_result){0};

    if (length >= ONE_G02_OFFSET_DISPATCH_BYTES) {
        out->selected_offset_path = 1;
        return one_g02_minimizer_offset_only_kernel(
            data, length, gear, window, minimizer_span,
            (one_g02_offset_only_result *)out, trace, trace_capacity
        );
    }

    out->selected_offset_path = 0;
    return one_g02_minimizer_segmented_counter_kernel(
        data, length, gear, window, minimizer_span,
        (one_g02_segmented_counter_result *)out, trace, trace_capacity
    );
}
