#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define main one_g02_prev_hierarchy_main
#include "one_g02_hierarchy_first_level_fusion.c"
#undef main

static uint64_t hv_ns_now(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0u;
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int validate_seed(const one_g02_segment *segments, size_t segment_count,
                         size_t source_len, size_t target_len,
                         size_t *surprise_count_out) {
    if (!segments || segment_count == 0u) return -3;
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -2;
    if (segment_count > target_len) return -3;
    size_t surprises = 0u, covered = 0u;
    for (size_t i = 0; i < segment_count; ++i) {
        const size_t start = (size_t)segments[i].start;
        const size_t length = (size_t)segments[i].length;
        if (length == 0u) return -4;
        if (segments[i].kind == 0u) {
            if (start > source_len || length > source_len - start) return -5;
        } else if (segments[i].kind == 1u) {
            if (start > target_len || length > target_len - start) return -6;
            ++surprises;
        } else {
            return -8;
        }
        if (length > target_len - covered) return -9;
        covered += length;
    }
    if (covered != target_len) return -10;
    size_t intermediate_total = 0u, depth = 1u, level_count = segment_count;
    while (level_count > ONE_MAX_NODES) {
        level_count = (level_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        if (level_count > SIZE_MAX - intermediate_total) return -11;
        intermediate_total += level_count;
        if (++depth > ONE_MAX_DEPTH) return -11;
    }
    if (1u + surprises + intermediate_total + 1u > ONE_MAX_NODES) return -12;
    if (surprise_count_out) *surprise_count_out = surprises;
    return 0;
}

static int validate_capture_spans(const one_g02_segment *segments, size_t segment_count,
                                  size_t source_len, size_t target_len,
                                  uint64_t **group_spans_out, size_t *group_count_out,
                                  size_t *surprise_count_out) {
    if (!group_spans_out || !group_count_out) return -1;
    *group_spans_out = NULL;
    *group_count_out = 0u;
    if (!segments || segment_count == 0u) return -3;
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -2;
    if (segment_count > target_len) return -3;

    const size_t groups = parent_count(segment_count);
    uint64_t *spans = (uint64_t *)calloc(groups ? groups : 1u, sizeof(*spans));
    if (!spans) return -14;

    size_t surprises = 0u, covered = 0u, gi = 0u;
    uint64_t group_span = 0u;
    for (size_t i = 0; i < segment_count; ++i) {
        const size_t start = (size_t)segments[i].start;
        const size_t length = (size_t)segments[i].length;
        int rc = 0;
        if (length == 0u) rc = -4;
        else if (segments[i].kind == 0u) {
            if (start > source_len || length > source_len - start) rc = -5;
        } else if (segments[i].kind == 1u) {
            if (start > target_len || length > target_len - start) rc = -6;
            else ++surprises;
        } else rc = -8;
        if (rc != 0) { free(spans); return rc; }
        if (length > target_len - covered) { free(spans); return -9; }
        covered += length;
        group_span += (uint64_t)length;
        if (((i + 1u) % ONE_MAX_NODES) == 0u || i + 1u == segment_count) {
            if (gi >= groups) { free(spans); return -11; }
            spans[gi++] = group_span;
            group_span = 0u;
        }
    }
    if (covered != target_len) { free(spans); return -10; }

    size_t intermediate_total = 0u, depth = 1u, level_count = segment_count;
    while (level_count > ONE_MAX_NODES) {
        level_count = (level_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        if (level_count > SIZE_MAX - intermediate_total) { free(spans); return -11; }
        intermediate_total += level_count;
        if (++depth > ONE_MAX_DEPTH) { free(spans); return -11; }
    }
    if (1u + surprises + intermediate_total + 1u > ONE_MAX_NODES) {
        free(spans); return -12;
    }
    if (gi != groups) { free(spans); return -11; }
    *group_spans_out = spans;
    *group_count_out = groups;
    if (surprise_count_out) *surprise_count_out = surprises;
    return 0;
}

static int emit_with_captured_spans(one_out *o, const one_g02_segment *segments,
                                    size_t segment_count, size_t surprise_count,
                                    uint64_t target_len, const uint64_t *group_spans,
                                    size_t group_count) {
    if (!o || !segments || !group_spans || segment_count <= ONE_MAX_NODES) return -1;
    if (group_count != parent_count(segment_count)) return -1;
    one_level_ref *level = (one_level_ref *)malloc(group_count * sizeof(*level));
    if (!level) return -1;

    uint64_t next_surprise_node = 1u;
    uint64_t next_node = 1u + (uint64_t)surprise_count;
    size_t gi = 0u;
    for (size_t off = 0; off < segment_count; off += ONE_MAX_NODES, ++gi) {
        size_t chunk = segment_count - off;
        if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
        const uint64_t declared = group_spans[gi];
        if (put_concat_segment_chunk(o, segments + off, chunk, declared,
                                     &next_surprise_node) != 0) {
            free(level); return -2;
        }
        level[gi].node = next_node++;
        level[gi].start = 0u;
        level[gi].wire_length = 0u;
        level[gi].has_length = 0u;
        level[gi].span = declared;
    }
    if (gi != group_count || next_surprise_node != 1u + surprise_count) {
        free(level); return -3;
    }

    size_t nlevel = group_count;
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

static int valid_row(const char *name, size_t count, size_t surprise_stride, size_t rounds) {
    one_g02_segment *segments = (one_g02_segment *)calloc(count, sizeof(*segments));
    if (!segments) return 2;
    size_t surprises = 0u;
    size_t target_len = 0u;
    size_t source_len = count * 64u + 4096u;
    if (source_len > ONE_MAX_OUTPUT) source_len = ONE_MAX_OUTPUT;
    for (size_t i = 0; i < count; ++i) {
        const uint32_t len = (uint32_t)(1u + ((i * 17u + 3u) % 31u));
        segments[i].length = len;
        segments[i].kind = (surprise_stride && (i % surprise_stride) == 0u) ? 1u : 0u;
        segments[i].start = segments[i].kind ? (uint32_t)target_len : (uint32_t)((i * 37u) % (source_len - 64u));
        target_len += len;
        surprises += segments[i].kind == 1u;
    }
    if (target_len > ONE_MAX_OUTPUT || target_len < count) { free(segments); return 3; }

    const size_t cap = count * 32u + 1024u * 1024u;
    uint8_t *a = (uint8_t *)malloc(cap), *b = (uint8_t *)malloc(cap);
    if (!a || !b) { free(a); free(b); free(segments); return 2; }
    one_out oa = {a, 0u, cap}, ob = {b, 0u, cap};

    size_t scheck = 0u, ccheck = 0u, groups = 0u;
    uint64_t *spans = NULL;
    int sr = validate_seed(segments, count, source_len, target_len, &scheck);
    int cr = validate_capture_spans(segments, count, source_len, target_len, &spans, &groups, &ccheck);
    if (sr != 0 || cr != 0 || scheck != ccheck || scheck != surprises) {
        fprintf(stderr, "%s validation mismatch seed=%d candidate=%d surprise=%zu/%zu/%zu\n",
                name, sr, cr, scheck, ccheck, surprises);
        free(spans); free(a); free(b); free(segments); return 4;
    }
    if (seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0 ||
        emit_with_captured_spans(&ob, segments, count, surprises, target_len, spans, groups) != 0 ||
        oa.len != ob.len || memcmp(a, b, oa.len) != 0) {
        fprintf(stderr, "%s byte parity failure seed=%zu candidate=%zu\n", name, oa.len, ob.len);
        free(spans); free(a); free(b); free(segments); return 4;
    }
    free(spans);

    for (size_t i = 0; i < 6u; ++i) {
        size_t tmp = 0u, gc = 0u;
        uint64_t *gs = NULL;
        oa.len = 0u; ob.len = 0u;
        if (validate_seed(segments, count, source_len, target_len, &tmp) != 0 ||
            seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0 ||
            validate_capture_spans(segments, count, source_len, target_len, &gs, &gc, &tmp) != 0 ||
            emit_with_captured_spans(&ob, segments, count, surprises, target_len, gs, gc) != 0) {
            free(gs); free(a); free(b); free(segments); return 5;
        }
        free(gs);
    }

    uint64_t seed_ns = 0u, cand_ns = 0u;
    for (size_t r = 0; r < rounds; ++r) {
        size_t tmp = 0u, gc = 0u;
        uint64_t *gs = NULL;
        if ((r & 1u) == 0u) {
            oa.len = 0u; uint64_t t0 = hv_ns_now();
            if (validate_seed(segments, count, source_len, target_len, &tmp) != 0 ||
                seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0) return 5;
            seed_ns += hv_ns_now() - t0;
            ob.len = 0u; t0 = hv_ns_now();
            if (validate_capture_spans(segments, count, source_len, target_len, &gs, &gc, &tmp) != 0 ||
                emit_with_captured_spans(&ob, segments, count, surprises, target_len, gs, gc) != 0) return 5;
            free(gs); gs = NULL;
            cand_ns += hv_ns_now() - t0;
        } else {
            ob.len = 0u; uint64_t t0 = hv_ns_now();
            if (validate_capture_spans(segments, count, source_len, target_len, &gs, &gc, &tmp) != 0 ||
                emit_with_captured_spans(&ob, segments, count, surprises, target_len, gs, gc) != 0) return 5;
            free(gs); gs = NULL;
            cand_ns += hv_ns_now() - t0;
            oa.len = 0u; t0 = hv_ns_now();
            if (validate_seed(segments, count, source_len, target_len, &tmp) != 0 ||
                seed_emit_hierarchy(&oa, segments, count, surprises, target_len) != 0) return 5;
            seed_ns += hv_ns_now() - t0;
        }
    }

    const size_t parents = parent_count(count);
    const size_t seed_transient = (count + parents) * sizeof(one_level_ref);
    const size_t cand_transient = parents * (sizeof(one_level_ref) + sizeof(uint64_t));
    const double elapsed_ratio = seed_ns ? (double)cand_ns / (double)seed_ns : 0.0;
    printf("ROW name=%s segments=%zu groups=%zu wire=%zu seed_transient=%zu candidate_transient=%zu seed_ns=%llu candidate_ns=%llu elapsed_ratio=%.6f\n",
           name, count, parents, oa.len, seed_transient, cand_transient,
           (unsigned long long)seed_ns, (unsigned long long)cand_ns, elapsed_ratio);

    free(a); free(b); free(segments);
    return 0;
}

static int hostile_parity(void) {
    one_g02_segment one = {0u, 8u, 0u};
    one_g02_segment bad_zero = {0u, 0u, 0u};
    one_g02_segment bad_kind = {0u, 8u, 9u};
    one_g02_segment bad_ref = {32u, 8u, 0u};
    one_g02_segment bad_surprise = {32u, 8u, 1u};
    one_g02_segment short_cover = {0u, 7u, 0u};
    one_g02_segment over_cover = {0u, 9u, 0u};
    struct tc { const char *name; one_g02_segment *p; size_t src, dst; int want; } cases[] = {
        {"zero", &bad_zero, 8u, 8u, -4}, {"kind", &bad_kind, 8u, 8u, -8},
        {"ref-oob", &bad_ref, 32u, 8u, -5}, {"surprise-oob", &bad_surprise, 8u, 32u, -6},
        {"short", &short_cover, 8u, 8u, -10}, {"over", &over_cover, 16u, 8u, -9},
        {"valid", &one, 8u, 8u, 0}
    };
    for (size_t i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i) {
        size_t a = 0u, b = 0u, gc = 0u; uint64_t *spans = NULL;
        int sr = validate_seed(cases[i].p, 1u, cases[i].src, cases[i].dst, &a);
        int cr = validate_capture_spans(cases[i].p, 1u, cases[i].src, cases[i].dst, &spans, &gc, &b);
        free(spans);
        if (sr != cr || sr != cases[i].want) {
            fprintf(stderr, "HOSTILE %s seed=%d candidate=%d want=%d\n", cases[i].name, sr, cr, cases[i].want);
            return 1;
        }
    }
    puts("hostile validation rejection parity: PASS");
    return 0;
}

int main(void) {
    if (hostile_parity() != 0) return 1;
    int rc = 0;
    rc |= valid_row("hier-4097-ref", 4097u, 0u, 900u);
    rc |= valid_row("hier-4097-mixed", 4097u, 8u, 900u);
    rc |= valid_row("hier-16384-ref", 16384u, 0u, 320u);
    rc |= valid_row("hier-65536-mixed", 65536u, 32u, 100u);
    if (rc != 0) return rc;
    puts("hierarchy validation-span fusion diagnostic: semantic parity PASS");
    return 0;
}
