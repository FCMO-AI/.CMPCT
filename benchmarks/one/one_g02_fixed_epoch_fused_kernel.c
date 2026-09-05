#include <stddef.h>
#include <stdint.h>

/* ONE-G0.2 encoder-discovery research kernel.
 *
 * Fuses the already-required aligned fixed observation signal with starvation-epoch Gear
 * nomination in one byte-forward loop. It deliberately stops before index lookup/proof:
 * this kernel answers only whether eliminating the duplicate source scan is a real D2
 * execution win while preserving both signal traces exactly.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t sparse_anchors;
    uint64_t pulses;
    uint64_t reserved_state_bytes;
} one_g02_epoch_min_result;

typedef struct {
    uint64_t emitted;
    uint64_t bytes_scanned;
    uint64_t reserved_state_bytes;
} one_g02_fixed_signal_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)
#define ONE_G02_FNV64_OFFSET UINT64_C(0xcbf29ce484222325)
#define ONE_G02_FNV64_PRIME UINT64_C(0x100000001b3)

static int fixed_emit(
    uint64_t hash,
    uint64_t start,
    one_g02_fixed_signal_result *out,
    uint64_t *hash_trace,
    uint64_t *start_trace,
    size_t trace_capacity
) {
    if (hash_trace != NULL || start_trace != NULL) {
        if (out->emitted >= trace_capacity) return -4;
        if (hash_trace != NULL) hash_trace[out->emitted] = hash;
        if (start_trace != NULL) start_trace[out->emitted] = start;
    }
    out->emitted += 1;
    return 0;
}

static int epoch_emit(
    uint64_t min_position,
    one_g02_epoch_min_result *out,
    uint64_t *trace,
    size_t trace_capacity
) {
    if (min_position == UINT64_MAX) return 0;
    if (trace != NULL) {
        if (out->emitted >= trace_capacity) return -4;
        trace[out->emitted] = min_position;
    }
    out->emitted += 1;
    out->pulses += 1;
    return 0;
}

int one_g02_fixed_signal_kernel(
    const uint8_t *data,
    size_t length,
    size_t window,
    one_g02_fixed_signal_result *out,
    uint64_t *hash_trace,
    uint64_t *start_trace,
    size_t trace_capacity
) {
    if (out == NULL || window == 0) return -1;
    *out = (one_g02_fixed_signal_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    out->reserved_state_bytes = 4 * sizeof(uint64_t);
    uint64_t chunk_hash = ONE_G02_FNV64_OFFSET;
    uint8_t run_value = data[0];
    size_t run_length = 0;

    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (run_length == 0) { run_value = value; run_length = 1; }
        else if (value == run_value) { run_length += 1; }
        else { run_value = value; run_length = 1; }

        chunk_hash ^= (uint64_t)value;
        chunk_hash *= ONE_G02_FNV64_PRIME;
        out->bytes_scanned += 1;

        if ((position + 1) % window == 0) {
            uint64_t start = (uint64_t)(position + 1 - window);
            uint64_t fingerprint = chunk_hash;
            chunk_hash = ONE_G02_FNV64_OFFSET;
            int run_dominated = run_length >= (window > ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
            if (!run_dominated) {
                int rc = fixed_emit(fingerprint, start, out, hash_trace, start_trace, trace_capacity);
                if (rc) return rc;
            }
        }
    }
    return 0;
}

int one_g02_fixed_epoch_fused_kernel(
    const uint8_t *data,
    size_t length,
    const uint64_t gear[256],
    size_t window,
    size_t span,
    one_g02_fixed_signal_result *fixed_out,
    one_g02_epoch_min_result *epoch_out,
    uint64_t *fixed_hash_trace,
    uint64_t *fixed_start_trace,
    size_t fixed_trace_capacity,
    uint64_t *epoch_trace,
    size_t epoch_trace_capacity
) {
    if (fixed_out == NULL || epoch_out == NULL || gear == NULL || window == 0 || span == 0) return -1;
    *fixed_out = (one_g02_fixed_signal_result){0};
    *epoch_out = (one_g02_epoch_min_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    fixed_out->reserved_state_bytes = 4 * sizeof(uint64_t);
    epoch_out->reserved_state_bytes = (uint64_t)(256 * sizeof(uint64_t)) + (uint64_t)(5 * sizeof(uint64_t));

    uint64_t chunk_hash = ONE_G02_FNV64_OFFSET;
    uint64_t state = 0;
    uint64_t last_sparse_position = UINT64_MAX;
    uint64_t min_signal = UINT64_MAX;
    uint64_t min_position = UINT64_MAX;
    uint64_t epoch_count = 0;
    int active = 0;
    uint8_t run_value = data[0];
    size_t run_length = 0;

    for (size_t position = 0; position < length; ++position) {
        uint8_t value = data[position];
        if (run_length == 0) { run_value = value; run_length = 1; }
        else if (value == run_value) { run_length += 1; }
        else { run_value = value; run_length = 1; }

        /* Fixed observation signal. */
        chunk_hash ^= (uint64_t)value;
        chunk_hash *= ONE_G02_FNV64_PRIME;
        fixed_out->bytes_scanned += 1;
        if ((position + 1) % window == 0) {
            uint64_t start = (uint64_t)(position + 1 - window);
            uint64_t fingerprint = chunk_hash;
            chunk_hash = ONE_G02_FNV64_OFFSET;
            int run_dominated = run_length >= (window > ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
            if (!run_dominated) {
                int rc = fixed_emit(fingerprint, start, fixed_out, fixed_hash_trace, fixed_start_trace, fixed_trace_capacity);
                if (rc) return rc;
            }
        }

        /* Epoch-min Gear signal, semantically identical to the standalone kernel. */
        state = (state << 1) + gear[value];
        if (position + 1 < window) continue;
        epoch_out->positions_considered += 1;

        int run_dominated = run_length >= (window > ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
        int sparse_anchor = ((state & ONE_G02_ANCHOR_MASK) == 0) && !run_dominated;
        if (sparse_anchor) {
            if (active) {
                int rc = epoch_emit(min_position, epoch_out, epoch_trace, epoch_trace_capacity);
                if (rc) return rc;
            }
            epoch_out->sparse_anchors += 1;
            last_sparse_position = (uint64_t)position;
            active = 0;
            min_signal = UINT64_MAX;
            min_position = UINT64_MAX;
            epoch_count = 0;
            continue;
        }
        if (run_dominated) continue;

        epoch_count += 1;
        if (state <= min_signal) {
            min_signal = state;
            min_position = (uint64_t)position;
        }

        uint64_t gap = last_sparse_position == UINT64_MAX
            ? (uint64_t)(position + 1 - window)
            : (uint64_t)position - last_sparse_position;
        if (!active && gap >= (uint64_t)span) {
            int rc = epoch_emit(min_position, epoch_out, epoch_trace, epoch_trace_capacity);
            if (rc) return rc;
            min_signal = UINT64_MAX;
            min_position = UINT64_MAX;
            epoch_count = 0;
            active = 1;
        } else if (active && epoch_count >= (uint64_t)span) {
            int rc = epoch_emit(min_position, epoch_out, epoch_trace, epoch_trace_capacity);
            if (rc) return rc;
            min_signal = UINT64_MAX;
            min_position = UINT64_MAX;
            epoch_count = 0;
        }
    }

    if (active) {
        int rc = epoch_emit(min_position, epoch_out, epoch_trace, epoch_trace_capacity);
        if (rc) return rc;
    }
    epoch_out->final_state = state;
    return 0;
}
