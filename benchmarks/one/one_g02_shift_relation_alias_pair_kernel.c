#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

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
} one_g02_alias_result;

typedef struct {
    double direct_ns_per_call;
    double restrict_ns_per_call;
    double half_ns_per_call;
    one_g02_alias_result direct_result;
    one_g02_alias_result restrict_result;
    one_g02_alias_result half_result;
} one_g02_alias_measurement;

extern int one_g02_shift_branch_bound_relation_direct(
    const uint8_t *, const uint8_t *, size_t, one_g02_alias_result *);
extern int one_g02_shift_branch_bound_relation_restrict(
    const uint8_t *, const uint8_t *, size_t, one_g02_alias_result *);
extern int one_g02_shift_branch_bound_proof_led(
    const uint8_t *, size_t, one_g02_alias_result *);

static uint64_t ns_now_alias(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int one_g02_shift_relation_alias_measure(
    const uint8_t *packed, size_t relation_len, size_t batch_calls,
    one_g02_alias_measurement *out)
{
    if (!packed || !out || relation_len < 1024 || batch_calls == 0) return -1;
    const uint8_t *src = packed, *dst = packed + relation_len;
    const size_t packed_len = relation_len * 2;
    one_g02_alias_result dr = {0}, rr = {0}, hr = {0};
    if (one_g02_shift_branch_bound_relation_direct(src, dst, relation_len, &dr) != 0) return -2;
    if (one_g02_shift_branch_bound_relation_restrict(src, dst, relation_len, &rr) != 0) return -3;
    if (one_g02_shift_branch_bound_proof_led(packed, packed_len, &hr) != 0) return -4;

    uint64_t t0, d1, d2, r1, r2, r3, r4, h1, h2;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,&dr);
    d1 = ns_now_alias()-t0;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_relation_restrict(src,dst,relation_len,&rr);
    r1 = ns_now_alias()-t0;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_relation_restrict(src,dst,relation_len,&rr);
    r2 = ns_now_alias()-t0;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,&dr);
    d2 = ns_now_alias()-t0;

    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_proof_led(packed,packed_len,&hr);
    h1 = ns_now_alias()-t0;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_relation_restrict(src,dst,relation_len,&rr);
    r3 = ns_now_alias()-t0;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_relation_restrict(src,dst,relation_len,&rr);
    r4 = ns_now_alias()-t0;
    t0 = ns_now_alias();
    for (size_t i=0;i<batch_calls;++i) one_g02_shift_branch_bound_proof_led(packed,packed_len,&hr);
    h2 = ns_now_alias()-t0;

    out->direct_ns_per_call = ((double)d1+(double)d2)/(2.0*(double)batch_calls);
    out->restrict_ns_per_call = ((double)r1+(double)r2+(double)r3+(double)r4)/(4.0*(double)batch_calls);
    out->half_ns_per_call = ((double)h1+(double)h2)/(2.0*(double)batch_calls);
    out->direct_result=dr; out->restrict_result=rr; out->half_result=hr;
    return 0;
}
