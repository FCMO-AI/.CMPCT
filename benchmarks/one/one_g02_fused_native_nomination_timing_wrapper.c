#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

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
    uint64_t cross_auditions;
    uint64_t cross_exact;
    uint64_t local_peak_entries;
    uint64_t global_peak_entries;
    uint64_t verification_read_bytes;
    uint64_t extension_read_bytes;
    uint64_t anchors_consumed;
} one_g02_nomination_consumer_result;

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads;
    uint64_t cross_auditions;
    uint64_t cross_exact;
    uint64_t local_peak_entries;
    uint64_t global_peak_entries;
    uint64_t verification_read_bytes;
    uint64_t extension_read_bytes;
} one_g02_fused_nomination_result;

int one_g02_minimizer_offset_only_kernel(
    const uint8_t *, size_t, const uint64_t[256], size_t, size_t,
    one_g02_offset_only_result *, uint64_t *, size_t
);
int one_g02_native_nomination_event_consumer(
    const uint8_t *, size_t, size_t, const uint64_t[256],
    const uint64_t *, size_t, one_g02_nomination_consumer_result *
);
int one_g02_fused_native_nomination(
    const uint8_t *, size_t, size_t, const uint64_t[256], size_t, size_t,
    one_g02_fused_nomination_result *, uint64_t *, size_t
);

typedef struct {
    uint64_t anchors;
    uint64_t cross_auditions;
    uint64_t cross_exact;
    uint64_t final_state;
} one_g02_timing_summary;

int one_g02_timing_selector_only(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_timing_summary *out
) {
    one_g02_offset_only_result result = {0};
    int rc = one_g02_minimizer_offset_only_kernel(
        data, length, gear, window, minimizer_span, &result, NULL, 0
    );
    if (rc != 0) return rc;
    out->anchors = result.emitted;
    out->cross_auditions = 0;
    out->cross_exact = 0;
    out->final_state = result.final_state;
    return 0;
}

int one_g02_timing_two_stage(
    const uint8_t *data,
    size_t length,
    size_t boundary,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_timing_summary *out
) {
    uint64_t *trace = (uint64_t *)malloc((length + 1) * sizeof(uint64_t));
    if (trace == NULL) return -20;
    one_g02_offset_only_result selector = {0};
    int rc = one_g02_minimizer_offset_only_kernel(
        data, length, gear, window, minimizer_span, &selector, trace, length + 1
    );
    if (rc != 0) {
        free(trace);
        return rc;
    }
    one_g02_nomination_consumer_result consumer = {0};
    rc = one_g02_native_nomination_event_consumer(
        data, length, boundary, gear, trace, (size_t)selector.emitted, &consumer
    );
    free(trace);
    if (rc != 0) return rc;
    out->anchors = selector.emitted;
    out->cross_auditions = consumer.cross_auditions;
    out->cross_exact = consumer.cross_exact;
    out->final_state = selector.final_state;
    return 0;
}

int one_g02_timing_fused(
    const uint8_t *data,
    size_t length,
    size_t boundary,
    const uint64_t gear[256],
    size_t window,
    size_t minimizer_span,
    one_g02_timing_summary *out
) {
    one_g02_fused_nomination_result result = {0};
    int rc = one_g02_fused_native_nomination(
        data, length, boundary, gear, window, minimizer_span, &result, NULL, 0
    );
    if (rc != 0) return rc;
    out->anchors = result.emitted;
    out->cross_auditions = result.cross_auditions;
    out->cross_exact = result.cross_exact;
    out->final_state = result.final_state;
    return 0;
}
