/* O166 source-independent, deterministic pthread cold-start CDC differential harness.
 * Research only. Every variant links its own unmodified native/cmpct_cdc.c.
 * Output digest is a compact deterministic cut receipt, not a performance result.
 */
#define _GNU_SOURCE
#include <pthread.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <inttypes.h>

extern size_t cmpct_cdc_cut(const uint8_t *data, size_t n, size_t min_size,
                            size_t avg_size, size_t max_size, uint64_t *out,
                            size_t cap);

enum { WORKERS = 24, REPETITIONS = 48, PAYLOAD = 8192 };
static pthread_barrier_t start_line;
static atomic_uint_fast64_t folded = 0;
static atomic_int bad = 0;

static uint64_t mix(uint64_t v) {
    v ^= v >> 30; v *= UINT64_C(0xbf58476d1ce4e5b9);
    v ^= v >> 27; v *= UINT64_C(0x94d049bb133111eb);
    return v ^ (v >> 31);
}
static void *worker(void *arg) {
    uintptr_t id = (uintptr_t)arg;
    uint8_t input[PAYLOAD];
    uint64_t ends[PAYLOAD];
    uint64_t x = mix(id + UINT64_C(0x1234567812345678));
    for (size_t i = 0; i < PAYLOAD; ++i) {
        x = x * UINT64_C(6364136223846793005) + 1;
        input[i] = (uint8_t)(x >> 37);
    }

    int rc = pthread_barrier_wait(&start_line);
    if (rc != 0 && rc != PTHREAD_BARRIER_SERIAL_THREAD) {
        atomic_store(&bad, 1); return NULL;
    }
    uint64_t folded_local = mix(id);
    for (unsigned rep = 0; rep < REPETITIONS; ++rep) {
        const size_t n = cmpct_cdc_cut(input, PAYLOAD, 64, 256, 1024,
                                       ends, PAYLOAD);
        if (n == 0 || n > PAYLOAD || ends[n-1] != PAYLOAD) {
            atomic_store(&bad, 1); return NULL;
        }
        uint64_t prev = 0;
        for (size_t j = 0; j < n; ++j) {
            if (ends[j] <= prev || ends[j] > PAYLOAD ||
                ends[j] - prev > 1024) {
                atomic_store(&bad, 1); return NULL;
            }
            folded_local = mix(folded_local ^ (ends[j] + j + n));
            prev = ends[j];
        }
        folded_local = mix(folded_local ^ (n + rep));
    }
    atomic_fetch_xor(&folded, folded_local);
    return NULL;
}

int main(void) {
    pthread_t th[WORKERS];
    if (pthread_barrier_init(&start_line, NULL, WORKERS) != 0) return 90;
    for (uintptr_t k = 0; k < WORKERS; ++k) {
        if (pthread_create(&th[k], NULL, worker, (void *)k) != 0) return 91;
    }
    for (unsigned k = 0; k < WORKERS; ++k) {
        if (pthread_join(th[k], NULL) != 0) return 92;
    }
    if (atomic_load(&bad)) return 93;
    printf("O166_CDC_EXACT_FOLD=%016" PRIxFAST64 "\n", atomic_load(&folded));
    pthread_barrier_destroy(&start_line);
    return 0;
}
