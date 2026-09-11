#include <stddef.h>
#include <stdint.h>
#include <limits.h>

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
} one_g02_safe_dispatch_result;

extern int one_g02_shift_branch_bound_relation_direct(
    const uint8_t *, const uint8_t *, size_t, one_g02_safe_dispatch_result *);
extern int one_g02_shift_branch_bound_relation_restrict(
    const uint8_t *, const uint8_t *, size_t, one_g02_safe_dispatch_result *);

static int span_end(uintptr_t start, size_t len, uintptr_t *end) {
    if ((uintmax_t)len > (uintmax_t)UINTPTR_MAX) return 0;
    if (start > UINTPTR_MAX - (uintptr_t)len) return 0;
    *end = start + (uintptr_t)len;
    return 1;
}

static int spans_disjoint(const void *a, size_t an, const void *b, size_t bn) {
    uintptr_t as=(uintptr_t)a, bs=(uintptr_t)b, ae=0, be=0;
    if (!span_end(as,an,&ae) || !span_end(bs,bn,&be)) return 0;
    return ae <= bs || be <= as;
}

/* Returns 1 when the proven-disjoint no-alias path executed, 0 for the safe
 * generic fallback, and a negative value on invalid input. The caller may
 * ignore the path bit; relation semantics are identical either way.
 */
int one_g02_shift_relation_safe_dispatch(
    const uint8_t *src, const uint8_t *dst, size_t relation_len,
    one_g02_safe_dispatch_result *out)
{
    if (!out) return -1;
    if (!src || !dst || relation_len < 1024)
        return one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,out) == 0 ? 0 : -2;

    const int src_dst = spans_disjoint(src,relation_len,dst,relation_len);
    const int src_out = spans_disjoint(src,relation_len,out,sizeof(*out));
    const int dst_out = spans_disjoint(dst,relation_len,out,sizeof(*out));
    if (src_dst && src_out && dst_out) {
        if (one_g02_shift_branch_bound_relation_restrict(src,dst,relation_len,out) != 0) return -3;
        return 1;
    }
    if (one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,out) != 0) return -4;
    return 0;
}
