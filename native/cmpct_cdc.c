/* CMPCT content-defined chunker prototype.
 *
 * Footnote: chunk boundaries depend on the bytes around each boundary, not absolute file offsets.
 * This means inserting/deleting bytes usually changes only nearby chunks instead of invalidating every
 * later chunk. The container stores each chunk's explicit logical length, so readers do not depend on
 * this algorithm at all; future chunkers can coexist without changing the on-disk read contract.
 */
#include <stdint.h>
#include <stddef.h>

static uint64_t gear[256];
static int initialized = 0;

static uint64_t splitmix64(uint64_t *x) {
    uint64_t z = (*x += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static void init_gear(void) {
    if (initialized) return;
    uint64_t s = UINT64_C(0x434d504354434443); /* "CMPCTCDC" seed. */
    for (unsigned i = 0; i < 256; ++i) gear[i] = splitmix64(&s);
    initialized = 1;
}

/* Return number of chunks and write cumulative end offsets to out[].
 * avg must be a power of two. The two-mask normalization keeps chunks away from pathological
 * tiny/huge tails while preserving locality: fewer cuts before avg, more cuts after avg.
 */
size_t cmpct_cdc_cut(const uint8_t *data, size_t n, size_t min_size, size_t avg_size,
                     size_t max_size, uint64_t *out, size_t cap) {
    init_gear();
    if (!data || !out || cap == 0 || min_size == 0 || avg_size < min_size || max_size < avg_size)
        return 0;
    if ((avg_size & (avg_size - 1)) != 0) return 0;

    const uint64_t mask_early = (uint64_t)(avg_size * 2 - 1);
    const uint64_t mask_late  = (uint64_t)(avg_size / 2 - 1);
    size_t count = 0, start = 0;
    while (start < n) {
        size_t hard_end = start + max_size;
        if (hard_end > n) hard_end = n;
        size_t i = start + min_size;
        if (i >= hard_end) {
            if (count >= cap) return 0;
            out[count++] = hard_end; start = hard_end; continue;
        }
        size_t normal = start + avg_size;
        if (normal > hard_end) normal = hard_end;
        uint64_t h = 0;
        size_t cut = hard_end;
        for (; i < hard_end; ++i) {
            h = (h << 1) + gear[data[i]];
            uint64_t mask = (i < normal) ? mask_early : mask_late;
            if ((h & mask) == 0) { cut = i + 1; break; }
        }
        if (count >= cap) return 0;
        out[count++] = cut;
        start = cut;
    }
    return count;
}
