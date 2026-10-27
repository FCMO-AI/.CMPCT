/* J24N03: observational, source-exact x86/x64 CDC mask-width court.
 * This file records historical geometry, NOT a recommended portable contract.
 * Link only the unmodified source blob 216189c6a15f1579d596bc4df5128ae63f794168.
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <inttypes.h>

size_t cmpct_cdc_cut(const uint8_t *, size_t, size_t, size_t, size_t, uint64_t *, size_t);

static int valid(const uint64_t *ends, size_t count, size_t n) {
    uint64_t prev = 0;
    if (!count || count > 4) return 0;
    for (size_t i = 0; i < count; ++i) {
        if (ends[i] <= prev || ends[i] > (uint64_t)n) return 0;
        prev = ends[i];
    }
    return prev == (uint64_t)n;
}

int main(void) {
    static const uint8_t witness[7] = {0x00,0xde,0x1a,0x53,0xf0,0x11,0x63};
    uint64_t ends[4] = {0,0,0,0};
    if (sizeof(size_t) != 4 && sizeof(size_t) != 8) {
        fputs("J24N03 UNSUPPORTED unexpected size_t width\n", stderr);
        return 2;
    }
    size_t count = cmpct_cdc_cut(witness,7,1,1,7,ends,4);
    printf("J24N03 width_bits=%zu witness_count=%zu",sizeof(size_t)*8,count);
    for (size_t i=0; i<count && i<4; ++i)
        printf(" end[%zu]=%" PRIu64,i,ends[i]);
    putchar('\n');
    if (!valid(ends,count,7)) {
        fputs("J24N03 FAIL invalid witness partition\n",stderr);
        return 1;
    }
    if (sizeof(size_t) == 4) {
        if (count != 2 || ends[0] != 5 || ends[1] != 7) {
            fputs("J24N03 FALSIFIED predicted x86 [5,7]\n",stderr);
            return 1;
        }
    } else {
        if (count != 1 || ends[0] != 7) {
            fputs("J24N03 FALSIFIED predicted x64 [7]\n",stderr);
            return 1;
        }
    }
    uint64_t control[4] = {0,0,0,0};
    size_t cc = cmpct_cdc_cut(witness,7,1,2,7,control,4);
    if (!valid(control,cc,7)) {
        fputs("J24N03 FAIL avg=2 positive control partition\n",stderr);
        return 1;
    }
    printf("J24N03 avg2_control_count=%zu",cc);
    for (size_t i=0;i<cc;++i)
        printf(" end[%zu]=%" PRIu64,i,control[i]);
    putchar('\n');
    puts("J24N03 HOSTED_ORIGINAL_SOURCE_WIDTH_ORACLE PASS");
    return 0;
}
