#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* Research-only content-defined boundary scanner.
 *
 * The rolling gear state is content-derived and independent of paths/workload identity.
 * It emits little-endian u64 exclusive chunk-end offsets.  MIN/AVG/MAX are fixed by
 * the calling oracle and every chunk is bounded by MAX, making decode-unit accounting
 * explicit. Compilation is setup, not candidate creation; helper execution is timed.
 */

static uint64_t mix_byte(uint8_t x) {
    uint64_t z = (uint64_t)x + UINT64_C(0x9e3779b97f4a7c15);
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static int put_u64_le(uint64_t v) {
    unsigned char b[8];
    for (unsigned i = 0; i < 8; ++i) b[i] = (unsigned char)(v >> (8u * i));
    return fwrite(b, 1, 8, stdout) == 8 ? 0 : -1;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "usage: %s FILE MIN MASK MAX\n", argv[0]);
        return 2;
    }
    const uint64_t min_chunk = strtoull(argv[2], NULL, 0);
    const uint64_t mask = strtoull(argv[3], NULL, 0);
    const uint64_t max_chunk = strtoull(argv[4], NULL, 0);
    if (!min_chunk || max_chunk < min_chunk) return 2;

    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        fprintf(stderr, "open failed: %s\n", argv[1]);
        return 3;
    }
    uint64_t absolute = 0, chunk = 0, gear = 0;
    unsigned char buf[1 << 16];
    for (;;) {
        const size_t n = fread(buf, 1, sizeof(buf), f);
        for (size_t i = 0; i < n; ++i) {
            gear = (gear << 1) + mix_byte(buf[i]);
            ++absolute;
            ++chunk;
            if (chunk >= min_chunk && (((gear & mask) == 0) || chunk >= max_chunk)) {
                if (put_u64_le(absolute) != 0) return 4;
                chunk = 0;
                gear = 0;
            }
        }
        if (n < sizeof(buf)) {
            if (ferror(f)) return 5;
            break;
        }
    }
    fclose(f);
    if (chunk != 0) {
        if (put_u64_le(absolute) != 0) return 4;
    }
    return fflush(stdout) == 0 ? 0 : 4;
}
