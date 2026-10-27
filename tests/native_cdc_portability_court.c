/* J24N04: source-linked portable 32/64-bit CDC output geometry acceptance.
 * Historical divergent evidence stays frozen in J24N03; this suite asserts
 * the NEW contract, including held-out n>max and #608 boundary preservation.
 */
#include <stdint.h>
#include <stddef.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

size_t cmpct_cdc_cut(const uint8_t *, size_t, size_t, size_t, size_t, uint64_t *, size_t);

#define CAP 4096
static uint8_t input[CAP];
static uint64_t ends[CAP];
static uint64_t hash = UINT64_C(14695981039346656037);

static int fail(const char *reason) {
    fprintf(stderr, "J24N04 FAIL %s\n", reason);
    return 1;
}
static void fold(uint64_t v) {
    for (unsigned i = 0; i < 8; ++i) {
        hash ^= (uint8_t)(v >> (8 * i));
        hash *= UINT64_C(1099511628211);
    }
}
static int check(size_t count, size_t n, size_t max) {
    if (count == 0 || count > CAP) return fail("no complete partition");
    uint64_t previous = 0;
    for (size_t i = 0; i < count; ++i) {
        if (ends[i] <= previous || ends[i] > (uint64_t)n ||
            ends[i] - previous > (uint64_t)max) return fail("nonmonotone / out-of-bounds cut");
        previous = ends[i];
    }
    if (previous != (uint64_t)n) return fail("last cut does not equal input length");
    return 0;
}
static void populate(size_t n, uint32_t seed) {
    uint32_t x = seed | UINT32_C(1);
    for (size_t i = 0; i < n; ++i) {
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        input[i] = (uint8_t)x;
    }
}
int main(void) {
    volatile size_t width = sizeof(size_t); /* MSVC C4127: runtime width probe */
    if (width != 4 && width != 8) return fail("unsupported size_t bitness");
    static const uint8_t witness[7] = {0x00,0xde,0x1a,0x53,0xf0,0x11,0x63};
    size_t count = cmpct_cdc_cut(witness, 7, 1, 1, 7, ends, CAP);
    if (check(count,7,7) || count != 1 || ends[0] != 7)
        return fail("portable avg=1 witness differs from [7]");
    count = cmpct_cdc_cut(witness, 7, 1, 2, 7, ends, CAP);
    if (check(count,7,7) || count != 3 || ends[0]!=2 || ends[1]!=5 || ends[2]!=7)
        return fail("avg=2 historical positive control changed");
    printf("J24N04 witness=[7] avg2=[2,5,7] width_bits=%zu\n", width*8);

    /* A cross-width exact transcript: all parameters fit both x86 and x64.
     * Mix n<=max, n>max, early/late masks, unaligned limits and repeated data.
     * Hash count and cumulative ends with explicit LE byte serialization.
     */
    const size_t lengths[] = {7, 48, 63, 127, 511, 2047, 4095};
    unsigned long long cases = 0;
    for (uint32_t seed = 1; seed <= 23; ++seed) {
        for (size_t li = 0; li < sizeof(lengths)/sizeof(lengths[0]); ++li) {
            size_t n = lengths[li];
            populate(n, seed*UINT32_C(0x9e3779b9) + (uint32_t)li);
            for (size_t avg = 1; avg <= 256; avg *= 2) {
                size_t min = avg == 1 ? 1 : avg / 2;
                for (size_t scale = 1; scale <= 4; scale *= 2) {
                    size_t max = avg * scale;
                    count = cmpct_cdc_cut(input,n,min,avg,max,ends,CAP);
                    if (check(count,n,max)) return 1;
                    fold((uint64_t)seed);
                    fold((uint64_t)n);
                    fold((uint64_t)avg);
                    fold((uint64_t)max);
                    fold((uint64_t)count);
                    for (size_t k=0; k<count; ++k) fold(ends[k]);
                    ++cases;
                }
            }
        }
    }
    /* #608 boundary court: a huge max must not overflow start+max. */
    populate(48, UINT32_C(0x33333333));
    count = cmpct_cdc_cut(input, 48, 1, 2, SIZE_MAX, ends, CAP);
    if (check(count,48,SIZE_MAX)) return 1;
    size_t bounded_count = cmpct_cdc_cut(input,48,1,2,48,ends + 256,CAP - 256);
    if (!bounded_count || count != bounded_count ||
        memcmp(ends, ends+256, count*sizeof(uint64_t)) != 0)
        return fail("SIZE_MAX differs from bounded equivalent");
    /* No partial result when caller supplies too few output slots. */
    populate(128, 177);
    count = cmpct_cdc_cut(input,128,1,2,2,ends,CAP);
    if (check(count,128,2)) return 1;
    if (count < 2 || cmpct_cdc_cut(input,128,1,2,2,ends,count-1) != 0)
        return fail("insufficient-cap contract weakened");

    printf("J24N04 PORTABLE_DIGEST %016" PRIx64 " cases=%llu\n", hash, cases);
    puts("J24N04 PORTABLE_NATIVE_CDC_COURT PASS");
    return 0;
}
