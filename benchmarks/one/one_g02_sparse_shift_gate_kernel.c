#include <stddef.h>
#include <stdint.h>

/* Cheap writer-only opportunity gate. It is not a Law or reader mechanism.
 * Probe eight deterministic 64-byte samples across the first half and ask
 * whether corresponding samples in the second half match within +/-2 bytes.
 * This is deliberately a sparse falsifier for small-shift temporal resemblance,
 * not a general resemblance index.
 */
typedef struct {
    uint64_t samples;
    uint64_t matched_samples;
    uint64_t compared_bytes;
    int64_t best_shift;
} one_g02_sparse_shift_gate_result;

static uint64_t h64(const uint8_t *p) {
    uint64_t h = 1469598103934665603ULL;
    for (size_t i=0;i<64;i++) { h ^= p[i]; h *= 1099511628211ULL; }
    return h;
}

int one_g02_sparse_shift_gate(const uint8_t *data, size_t n,
                              one_g02_sparse_shift_gate_result *out) {
    if (!out) return -1;
    *out = (one_g02_sparse_shift_gate_result){0};
    if (!data || n < 1024) return 0;
    const size_t half = n / 2;
    if (half < 256 || n-half < 256) return 0;
    uint64_t shift_hits[5] = {0,0,0,0,0};
    for (size_t s=0;s<8;s++) {
        /* interior deterministic positions, avoiding edge effects */
        size_t p = 96 + ((half - 192 - 64) * (s + 1)) / 9;
        if (p + 64 > half) continue;
        uint64_t a = h64(data + p);
        out->samples++;
        int any = 0;
        for (int d=-2; d<=2; d++) {
            int64_t q = (int64_t)half + (int64_t)p + d;
            if (q < 0 || (uint64_t)q + 64 > n) continue;
            out->compared_bytes += 64;
            if (h64(data + q) == a) { shift_hits[d+2]++; any=1; }
        }
        if (any) out->matched_samples++;
    }
    uint64_t best=0; int bestd=0;
    for (int i=0;i<5;i++) if (shift_hits[i] > best) { best=shift_hits[i]; bestd=i-2; }
    out->best_shift = bestd;
    return 0;
}
