#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <openssl/sha.h>

#define ONE_HASH_BYTES 32u
#define ONE_HASH_WORKER_STACK (64u * 1024u)

typedef struct {
    pthread_mutex_t mu;
    pthread_cond_t request_cv;
    pthread_cond_t done_cv;
    pthread_t thread;
    const uint8_t *target;
    size_t target_len;
    uint8_t *target_out;
    int has_job;
    int done;
    int stop;
    int worker_error;
    int initialized;
} one_hash_pair_state;

static one_hash_pair_state G;
static pthread_once_t G_ONCE = PTHREAD_ONCE_INIT;

static void *hash_worker(void *unused) {
    (void)unused;
    pthread_mutex_lock(&G.mu);
    for (;;) {
        while (!G.has_job && !G.stop)
            pthread_cond_wait(&G.request_cv, &G.mu);
        if (G.stop) {
            pthread_mutex_unlock(&G.mu);
            return NULL;
        }
        const uint8_t *p = G.target;
        const size_t n = G.target_len;
        uint8_t *out = G.target_out;
        G.has_job = 0;
        pthread_mutex_unlock(&G.mu);

        const int ok = SHA256(p, n, out) != NULL;

        pthread_mutex_lock(&G.mu);
        G.worker_error = ok ? 0 : 1;
        G.done = 1;
        pthread_cond_signal(&G.done_cv);
    }
}

static void init_once(void) {
    memset(&G, 0, sizeof(G));
    if (pthread_mutex_init(&G.mu, NULL) != 0) return;
    if (pthread_cond_init(&G.request_cv, NULL) != 0) return;
    if (pthread_cond_init(&G.done_cv, NULL) != 0) return;

    pthread_attr_t attr;
    if (pthread_attr_init(&attr) != 0) return;
    size_t stack = ONE_HASH_WORKER_STACK;
#ifdef PTHREAD_STACK_MIN
    if (stack < (size_t)PTHREAD_STACK_MIN) stack = (size_t)PTHREAD_STACK_MIN;
#endif
    if (pthread_attr_setstacksize(&attr, stack) != 0) {
        pthread_attr_destroy(&attr);
        return;
    }
    if (pthread_create(&G.thread, &attr, hash_worker, NULL) == 0)
        G.initialized = 1;
    pthread_attr_destroy(&attr);
}

/*
 * Compute the two independent canonical SHA-256 root identities concurrently.
 * Returns 0 on exact success.  This function owns no input and keeps no digest
 * cache: only one bounded helper executor persists across calls.
 *
 * Calls are intentionally single-flight. A wider creator executor can schedule
 * independent relations around this primitive; silently queueing concurrent calls
 * here would hide resource/backpressure behavior from evidence.
 */
int one_g02_hash_pair(const uint8_t *source, size_t source_len,
                      const uint8_t *target, size_t target_len,
                      uint8_t previous_out[ONE_HASH_BYTES],
                      uint8_t current_out[ONE_HASH_BYTES]) {
    if ((!source && source_len) || (!target && target_len) || !previous_out || !current_out)
        return -1;
    if (pthread_once(&G_ONCE, init_once) != 0 || !G.initialized)
        return -2;

    pthread_mutex_lock(&G.mu);
    if (G.stop || G.has_job) {
        pthread_mutex_unlock(&G.mu);
        return -4;
    }
    G.target = target;
    G.target_len = target_len;
    G.target_out = current_out;
    G.done = 0;
    G.worker_error = 0;
    G.has_job = 1;
    pthread_cond_signal(&G.request_cv);
    pthread_mutex_unlock(&G.mu);

    const int source_ok = SHA256(source, source_len, previous_out) != NULL;

    pthread_mutex_lock(&G.mu);
    while (!G.done)
        pthread_cond_wait(&G.done_cv, &G.mu);
    const int worker_error = G.worker_error;
    pthread_mutex_unlock(&G.mu);
    return (source_ok && !worker_error) ? 0 : -3;
}

size_t one_g02_hash_pair_worker_stack_bytes(void) {
    return ONE_HASH_WORKER_STACK;
}

/* Explicit process/test cleanup. No caller is required to invoke this during
 * normal reusable-writer operation. After shutdown, the process should not call
 * one_g02_hash_pair again because pthread_once intentionally cannot reinitialize. */
int one_g02_hash_pair_shutdown(void) {
    if (!G.initialized) return 0;
    pthread_mutex_lock(&G.mu);
    G.stop = 1;
    pthread_cond_signal(&G.request_cv);
    pthread_mutex_unlock(&G.mu);
    if (pthread_join(G.thread, NULL) != 0) return -1;
    G.initialized = 0;
    return 0;
}
