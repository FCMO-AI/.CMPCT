#include <stdint.h>
#include <stddef.h>
#include <stdint.h>
/* J24G103c: research-only exact cutpoint recurrence, source-locked to J24G103.
 * This is NOT a published CMPCT decoder or a general-purpose archive parser.
 * Avoid arithmetic overflow and buffer overrun; target is frozen to two sizes.
 */
size_t j24g103_scan_cuts(const unsigned char *raw, size_t len, const uint64_t *gear,
                        size_t target, size_t *ends, size_t capacity) {
  if (!raw || !gear || !ends || (target != 4096 && target != 16384)) return SIZE_MAX;
  uint64_t state = 0;
  size_t start = 0, count = 0;
  const size_t lo = target / 4, hi = target * 4;
  for (size_t i = 0; i < len; ++i) {
    state = (state << 1) + gear[raw[i]];
    size_t span = i + 1 - start;
    if (span >= lo && (((state & (target - 1)) == 0) || span >= hi)) {
      if (count >= capacity) return SIZE_MAX;
      ends[count++] = i + 1;
      start = i + 1;
      state = 0;
    }
  }
  if (start < len) {
    if (count >= capacity) return SIZE_MAX;
    ends[count++] = len;
  }
  return count;
}
