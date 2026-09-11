#include <stddef.h>
#include <stdint.h>

/*
 * ONE-G0.2 Builder: cheap size/opportunity gate over two internal discovery
 * representations of the same exact selector.  No reader-visible mechanism,
 * Law, Gear identity, source pass, window or minimizer semantics change.
 *
 * The 8192-byte boundary was selected mechanically by the preregistered paired
 * crossover map before this Builder existed.  Below it the promoted counter
 * suffix representation avoids offset-only startup debt; at/above it the
 * lower-state offset-only representation is used.
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
} one_g02_size_dispatch_result;

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

int one_g02_minimizer_size_dispatch_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_size_dispatch_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (out == NULL) return -1;
    *out = (one_g02_size_dispatch_result){0};

    if (length >= ONE_G02_OFFSET_DISPATCH_BYTES) {
        one_g02_offset_only_result inner = {0};
        int rc = one_g02_minimizer_offset_only_kernel(
            data, length, gear, window, minimizer_span, &inner, trace, trace_capacity
        );
        if (rc != 0) return rc;
        out->emitted = inner.emitted;
        out->final_state = inner.final_state;
        out->positions_considered = inner.positions_considered;
        out->reserved_state_bytes = inner.reserved_state_bytes;
        out->derived_state_reads = inner.derived_state_reads;
        out->suffix_blocks_built = inner.suffix_blocks_built;
        out->suffix_blocks_skipped_dead = inner.suffix_blocks_skipped_dead;
        out->suffix_value_indirect_loads = inner.suffix_value_indirect_loads;
        out->selected_offset_path = 1;
        return 0;
    }

    one_g02_segmented_counter_result inner = {0};
    int rc = one_g02_minimizer_segmented_counter_kernel(
        data, length, gear, window, minimizer_span, &inner, trace, trace_capacity
    );
    if (rc != 0) return rc;
    out->emitted = inner.emitted;
    out->final_state = inner.final_state;
    out->positions_considered = inner.positions_considered;
    out->reserved_state_bytes = inner.reserved_state_bytes;
    out->derived_state_reads = inner.derived_state_reads;
    out->suffix_blocks_built = inner.suffix_blocks_built;
    out->suffix_blocks_skipped_dead = inner.suffix_blocks_skipped_dead;
    out->suffix_value_indirect_loads = 0;
    out->selected_offset_path = 0;
    return 0;
}
