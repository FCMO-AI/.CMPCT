#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "one_g02_shared_native_writer_ref_fused.c"

static uint64_t ns_now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0u;
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int seed_emit_hierarchy(one_out *o, const one_g02_segment *segments,
                               size_t segment_count, size_t surprise_count,
                               uint64_t target_len) {
    one_level_ref *level = (one_level_ref *)malloc(segment_count * sizeof(*level));
    if (!level) return -1;
    uint64_t next_surprise_node = 1u;
    for (size_t i = 0; i < segment_count; ++i) {
        const one_g02_segment *s = &segments[i];
        if (s->kind == 0u) {
            level[i].node = 0u;
            level[i].start = s->start;
            level[i].wire_length = s->length;
            level[i].has_length = 1u;
        } else {
            level[i].node = next_surprise_node++;
            level[i].start = 0u;
            level[i].wire_length = 0u;
            level[i].has_length = 0u;
        }
        level[i].span = s->length;
    }

    uint64_t next_node = 1u + (uint64_t)surprise_count;
    size_t nlevel = segment_count;
    while (nlevel > ONE_MAX_NODES) {
        const size_t next_count = (nlevel + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        one_level_ref *next = (one_level_ref *)malloc(next_count * sizeof(*next));
        if (!next) { free(level); return -1; }
        size_t ni = 0u;
        for (size_t off = 0; off < nlevel; off += ONE_MAX_NODES) {
            size_t chunk = nlevel - off;
            if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
            uint64_t declared = 0u;
            for (size_t j = 0; j < chunk; ++j) declared += level[off + j].span;
            if (put_concat(o, level + off, chunk, declared) != 0) {
                free(next); free(level); return -2;
            }
            next[ni].node = next_node++;
            next[ni].start = 0u;
            next[ni].wire_length = 0u;
            next[ni].has_length = 0u;
            next[ni].span = declared;
            ++ni;
        }
        free(level);
        level = next;
        nlevel = next_count;
    }
    const int rc = put_concat(o, level, nlevel, target_len);
    free(level);
    return rc;
}

static int put_concat_segment_chunk(one_out *o, const one_g02_segment *segments,
                                    size_t count, uint64_t declared,
                                    uint64_t *next_surprise_node) {
    if (!next_surprise_node) return -1;
    if (put_byte(o, 1u) != 0) return -20;
    if (put_uvarint(o, declared + 1u) != 0) return -20;
    if (put_uvarint(o, (uint64_t)count) != 0) return -20;
    for (size_t i = 0; i < count; ++i) {
        const one_g02_segment *s = &segments[i];
        if (s->kind == 0u) {
            if (put_ref(o, 0u, s->start, 1u, s->length) != 0) return -20;
        } else {
            if (put_ref(o, (*next_surprise_node)++, 0u, 0u, 0u) != 0) return -20;
        }
    }
    return put_uvarint(o, 0u);
}

static int candidate_emit_hierarchy(one_out *o, const one_g02_segment *segments,
                                    size_t segment_count, size_t surprise_count,
                                    uint64_t target_len) {
    if (segment_count <= ONE_MAX_NODES) return -1;
    const size_t parent_count = (segment_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
    one_level_ref *level = (one_level_ref *)malloc(parent_count * sizeof(*level));
    if (!level) return -1;

    uint64_t next_surprise_node = 1u;
    uint64_t next_node = 1u + (uint64_t)surprise_count;
    size_t ni = 0u;
    for (size_t off = 0; off < segment_count; off += ONE_MAX_NODES) {
        size_t chunk = segment_count - off;
        if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
        uint64_t declared = 0u;
        for (size_t j = 0; j < chunk; ++j) declared += segments[off + j].length;
        if (put_concat_segment_chunk(o, segments + off, chunk, declared,
                                     &next_surprise_node) != 0) {
            free(level); return -2;
        }
        level[ni].node = next_node++;
        level[ni].start = 0u;
        level[ni].wire_length = 0u;
        level[ni].has_length = 0u;
        level[ni].span = declared;
        ++ni;
    }
    if (ni != parent_count || next_surprise_node != 1u + surprise_count) {
        free(level); return -3;
    }

    size_t nlevel = parent_count;
    while (nlevel > ONE_MAX_NODES) {
        const size_t next_count = (nlevel + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        one_level_ref *next = (one_level_ref *)malloc(next_count * sizeof(*next));
        if (!next) { free(level); return -1; }
        size_t nnext = 0u;
        for (size_t off = 0; off < nlevel; off += ONE_MAX_NODES) {
            size_t chunk = nlevel - off;
            if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
            uint64_t declared = 0u;
            for (size_t j = 0; j < chunk; ++j) declared += level[off + j].span;
            if (put_concat(o, level + off, chunk, declared) != 0) {
                free(next); free(level); return -2;
            }
            next[nnext].node = next_node++;
            next[nnext].start = 0u;
            next[nnext].wire_length = 0u;
            next[nnext].has_length = 0u;
            next[nnext].span = declared;
            ++nnext;
        }
        free(level);
        level = next;
        nlevel = next_count;
    }
    const int rc = put_concat(o, level, nlevel, target_len);
    free(level);
    return rc;
}

static size_t parent_count(size_t n) {
    return (n + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
}

static int run_row(const char *name, size_t count, size_t surprise_stride, size_t rounds) {
    one_g02_segment *segments = (one_g02_segment *)calloc(count, sizeof(*segments));
    if (!segments) return 2;
    size_t surprises = 0u;
    uint64_t target_len = 0u;
    for (size_t i = 0; i < count; ++i) {
        const uint32_t len = (uint32_t)(1u + ((i * 17u + 3u) % 31u));
        segments[i].start = (uint32_t)(i * 37u);
        segments[i].length = len;
        segments[i].kind = (surprise_stride && (i % surprise_stride) == 0u) ? 1u : 0u;
        surprises += segments[i].kind == 1u;
        target_len += len;
    }
    if (surprises + parent_count(count) + 2u > ONE_MAX_NODES) {
        fprintf(stderr, "%s invalid node budget surprises=%zu parents=%zu\n",
                name, surprises, parent_count(count));
        free(segments); return 3;
    }

    const size_t cap = count * 32u + 1024u * 1024u;
    uint8_t *a = (uint8_t *)malloc(cap);
    uint8_t *b = (uint8_t *)malloc(cap);
    if (!a || !b) { free(a); free(b); free(segments); return 2; }
    one_out oa = {a, 0u, cap}, ob = {b, 0u, cap};
    if (seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0 ||
        candidate_emit_hierarchy(&ob, segments, count, surprises, target_len) != 0 ||
        oa.len != ob.len || memcmp(a, b, oa.len) != 0) {
        fprintf(stderr, "%s byte parity failure seed=%zu candidate=%zu\n", name, oa.len, ob.len);
        free(a); free(b); free(segments); return 4;
    }

    for (size_t i = 0; i < 8u; ++i) {
        oa.len = 0u; ob.len = 0u;
        if (seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0 ||
            candidate_emit_hierarchy(&ob, segments, count, surprises, target_len) != 0) return 5;
    }

    uint64_t seed_ns = 0u, cand_ns = 0u;
    for (size_t r = 0; r < rounds; ++r) {
        if ((r & 1u) == 0u) {
            oa.len = 0u; uint64_t t0 = ns_now();
            if (seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0) return 5;
            seed_ns += ns_now() - t0;
            ob.len = 0u; t0 = ns_now();
            if (candidate_emit_hierarchy(&ob, segments, count, surprises, target_len) != 0) return 5;
            cand_ns += ns_now() - t0;
        } else {
            ob.len = 0u; uint64_t t0 = ns_now();
            if (candidate_emit_hierarchy(&ob, segments, count, surprises, target_len) != 0) return 5;
            cand_ns += ns_now() - t0;
            oa.len = 0u; t0 = ns_now();
            if (seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0) return 5;
            seed_ns += ns_now() - t0;
        }
    }

    const size_t parents = parent_count(count);
    const size_t seed_transient = (count + parents) * sizeof(one_level_ref);
    const size_t cand_transient = parents * sizeof(one_level_ref);
    const double elapsed_ratio = seed_ns ? (double)cand_ns / (double)seed_ns : 0.0;
    const double transient_ratio = seed_transient ? (double)cand_transient / (double)seed_transient : 0.0;
    printf("ROW name=%s segments=%zu surprises=%zu wire=%zu seed_transient=%zu candidate_transient=%zu transient_ratio=%.6f seed_ns=%llu candidate_ns=%llu elapsed_ratio=%.6f\n",
           name, count, surprises, oa.len, seed_transient, cand_transient, transient_ratio,
           (unsigned long long)seed_ns, (unsigned long long)cand_ns, elapsed_ratio);

    free(a); free(b); free(segments);
    return (elapsed_ratio > 1.0) ? 6 : 0;
}

int main(void) {
    int rc = 0;
    rc |= run_row("hier-4097-ref", 4097u, 0u, 1200u);
    rc |= run_row("hier-4097-mixed", 4097u, 8u, 1200u);
    rc |= run_row("hier-16384-ref", 16384u, 0u, 400u);
    rc |= run_row("hier-65536-mixed", 65536u, 32u, 120u);
    if (rc != 0) return rc;
    puts("hierarchy first-level fusion diagnostic: semantic parity PASS");
    return 0;
}
