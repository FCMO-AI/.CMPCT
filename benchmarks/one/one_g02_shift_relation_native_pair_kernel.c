#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

/* ONE-G0.2 native-internal timing discriminator.
 *
 * This harness removes Python/ctypes from the timed inner loop. It calls the
 * unchanged direct-pointer generic relation kernel and unchanged compact
 * half-layout kernel in ABBA batches from C, amortizing timer overhead across
 * many calls. No discovery or ONE representation semantics are changed.
 */
typedef struct {
    uint64_t samples;
    uint64_t zero_shift_matches;
    uint64_t coverage_compared_bytes;
    uint64_t best_hits;
    int64_t best_shift;
    uint64_t proof_attempts;
    uint64_t exact_proofs;
    uint64_t proof_compared_bytes;
    uint64_t strata_with_support;
} one_g02_native_pair_result;

typedef struct {
    double half_ns_per_call;
    double direct_ns_per_call;
    one_g02_native_pair_result half_result;
    one_g02_native_pair_result direct_result;
} one_g02_native_pair_measurement;

extern int one_g02_shift_branch_bound_relation_direct(
    const uint8_t *src, const uint8_t *dst, size_t relation_len,
    one_g02_native_pair_result *out);
extern int one_g02_shift_branch_bound_proof_led(
    const uint8_t *data, size_t n, one_g02_native_pair_result *out);

static uint64_t ns_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int one_g02_shift_relation_native_pair_measure(
    const uint8_t *packed, size_t relation_len, size_t batch_calls,
    one_g02_native_pair_measurement *out)
{
    if (!packed || !out || relation_len < 1024 || batch_calls == 0) return -1;
    const uint8_t *src = packed;
    const uint8_t *dst = packed + relation_len;
    const size_t packed_len = relation_len * 2;
    one_g02_native_pair_result hr = {0}, dr = {0};

    /* Warm both code paths and data identically before timing. */
    if (one_g02_shift_branch_bound_proof_led(packed, packed_len, &hr) != 0) return -2;
    if (one_g02_shift_branch_bound_relation_direct(src, dst, relation_len, &dr) != 0) return -3;

    uint64_t t0 = ns_now();
    for (size_t i = 0; i < batch_calls; ++i)
        one_g02_shift_branch_bound_proof_led(packed, packed_len, &hr);
    uint64_t h1 = ns_now() - t0;

    t0 = ns_now();
    for (size_t i = 0; i < batch_calls; ++i)
        one_g02_shift_branch_bound_relation_direct(src, dst, relation_len, &dr);
    uint64_t d1 = ns_now() - t0;

    t0 = ns_now();
    for (size_t i = 0; i < batch_calls; ++i)
        one_g02_shift_branch_bound_relation_direct(src, dst, relation_len, &dr);
    uint64_t d2 = ns_now() - t0;

    t0 = ns_now();
    for (size_t i = 0; i < batch_calls; ++i)
        one_g02_shift_branch_bound_proof_led(packed, packed_len, &hr);
    uint64_t h2 = ns_now() - t0;

    out->half_ns_per_call = ((double)h1 + (double)h2) / (2.0 * (double)batch_calls);
    out->direct_ns_per_call = ((double)d1 + (double)d2) / (2.0 * (double)batch_calls);
    out->half_result = hr;
    out->direct_result = dr;
    return 0;
}
