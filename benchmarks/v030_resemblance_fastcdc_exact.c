#include <stdint.h>
#include <stddef.h>

/*
 * Research-only exact accelerator for cmpct.resemblance.fastcdc().
 * All policy values, including the exact 256-entry Gear table and masks,
 * are supplied by Python. This function owns only the bounded hot loop.
 * It therefore cannot silently substitute the different historical
 * native/cmpct_cdc.c Gear table.
 */
size_t cmpct_resemblance_cut_exact(
    const uint8_t *data,
    size_t n,
    size_t min_size,
    size_t max_size,
    size_t normal_size,
    uint64_t small_mask,
    uint64_t large_mask,
    const uint64_t *gear,
    uint64_t *out,
    size_t cap
) {
    if (!data || !gear || !out || cap == 0 || min_size == 0 ||
        normal_size < min_size || max_size < normal_size) {
        return 0;
    }

    size_t count = 0;
    size_t start = 0;
    while (start < n) {
        size_t hard_end = start + max_size;
        if (hard_end < start || hard_end > n) hard_end = n;

        if (hard_end - start <= min_size) {
            if (count >= cap) return 0;
            out[count++] = (uint64_t)hard_end;
            break;
        }

        size_t i = start + min_size;
        uint64_t h = 0;
        size_t early_end = start + normal_size;
        if (early_end < start || early_end > hard_end) early_end = hard_end;
        size_t cut = 0;

        while (i < early_end) {
            h = (h << 1) + gear[data[i]];
            if ((h & small_mask) == 0) {
                cut = i + 1;
                break;
            }
            ++i;
        }

        if (cut == 0) {
            while (i < hard_end) {
                h = (h << 1) + gear[data[i]];
                if ((h & large_mask) == 0) {
                    cut = i + 1;
                    break;
                }
                ++i;
            }
        }

        if (cut == 0) cut = hard_end;
        if (cut <= start || cut > n || count >= cap) return 0;
        out[count++] = (uint64_t)cut;
        start = cut;
    }
    return count;
}
