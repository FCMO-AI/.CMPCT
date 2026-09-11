#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * Keep the authoritative ref-fused seed in this translation unit under renamed
 * entry points.  The candidate below therefore shares the exact canonical
 * emitter helpers with its baseline rather than maintaining a forked codec.
 */
#define one_g02_native_writer one_g02_native_writer_exact_capacity_seed
#define one_g02_native_writer_free one_g02_native_writer_exact_capacity_seed_free
#include "one_g02_shared_native_writer_ref_fused.c"
#undef one_g02_native_writer
#undef one_g02_native_writer_free

static int exact_addz(size_t *v, size_t n) {
    if (!v || n > SIZE_MAX - *v) return -1;
    *v += n;
    return 0;
}

static size_t exact_uvlen(uint64_t v) {
    size_t n = 1u;
    while (v >= 0x80u) { v >>= 7; ++n; }
    return n;
}

static int exact_add_uv(size_t *n, uint64_t v) {
    return exact_addz(n, exact_uvlen(v));
}

static int exact_add_blob(size_t *n, size_t len) {
    if (exact_add_uv(n, (uint64_t)len) != 0) return -1;
    return exact_addz(n, len);
}

static int exact_add_ref(size_t *n, uint64_t node, uint64_t start,
                         uint8_t has_length, uint64_t wire_length) {
    if (exact_add_uv(n, node) != 0 || exact_add_uv(n, start) != 0) return -1;
    return exact_add_uv(n, has_length ? wire_length + 1u : 0u);
}

static int exact_add_surprise(size_t *n, size_t len) {
    if (exact_addz(n, 1u) != 0 || exact_add_uv(n, 0u) != 0) return -1;
    return exact_add_blob(n, len);
}

static int exact_add_concat_head(size_t *n, uint64_t declared, size_t count) {
    if (exact_addz(n, 1u) != 0 || exact_add_uv(n, declared + 1u) != 0 ||
        exact_add_uv(n, (uint64_t)count) != 0) return -1;
    return 0;
}

/*
 * Exact-capacity candidate.
 *
 * Critical experiment invariant: checked_cap() is still called before the
 * exact allocation and remains the acceptance-domain authority.  The exact
 * counter only shrinks the allocation inside inputs the seed already accepts.
 * It never reads source/target payload bytes; all counting is derived from the
 * same segment metadata being semantically validated.
 */
int one_g02_native_writer_exact_capacity(
    const uint8_t *source, size_t source_len,
    const uint8_t *target, size_t target_len,
    const one_g02_segment *segments, size_t segment_count,
    const uint8_t previous_digest[32], const uint8_t current_digest[32],
    int enabled,
    uint8_t **out_data, size_t *out_len, size_t *surprise_bytes,
    size_t *allocated_bytes, size_t *hierarchy_depth_out, size_t *node_count_out) {

    if (!source || !target || !previous_digest || !current_digest || !out_data || !out_len ||
        !surprise_bytes || !allocated_bytes || !hierarchy_depth_out || !node_count_out)
        return -1;
    *out_data = NULL;
    *out_len = *surprise_bytes = *allocated_bytes = *hierarchy_depth_out = *node_count_out = 0u;
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -2;
    if ((enabled && (!segments || segment_count == 0u)) || (!enabled && segment_count != 0u)) return -3;
    if (segment_count > target_len) return -3;

    size_t surprise_count = 0u;
    size_t covered = 0u;
    size_t surprise_total = source_len;
    size_t exact_segment_surprises = 0u;
    size_t exact_segment_refs = 0u;

    /* Only hierarchy inputs need first-level spans for exact concat sizing. */
    const size_t first_count = enabled && segment_count > ONE_MAX_NODES
        ? (segment_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES : 0u;
    uint64_t *first_spans = NULL;
    if (first_count) {
        if (first_count > SIZE_MAX / sizeof(*first_spans)) return -11;
        first_spans = (uint64_t *)calloc(first_count, sizeof(*first_spans));
        if (!first_spans) return -14;
    }

    if (enabled) {
        for (size_t i = 0; i < segment_count; ++i) {
            const size_t start = (size_t)segments[i].start;
            const size_t length = (size_t)segments[i].length;
            if (length == 0u) { free(first_spans); return -4; }
            if (segments[i].kind == 0u) {
                if (start > source_len || length > source_len - start) { free(first_spans); return -5; }
                if (exact_add_ref(&exact_segment_refs, 0u, (uint64_t)start, 1u, (uint64_t)length) != 0) {
                    free(first_spans); return -13;
                }
            } else if (segments[i].kind == 1u) {
                if (start > target_len || length > target_len - start) { free(first_spans); return -6; }
                ++surprise_count;
                if (length > SIZE_MAX - surprise_total) { free(first_spans); return -7; }
                surprise_total += length;
                if (exact_add_surprise(&exact_segment_surprises, length) != 0 ||
                    exact_add_ref(&exact_segment_refs, (uint64_t)surprise_count, 0u, 0u, 0u) != 0) {
                    free(first_spans); return -13;
                }
            } else {
                free(first_spans); return -8;
            }
            if (length > target_len - covered) { free(first_spans); return -9; }
            covered += length;
            if (first_spans) {
                const size_t ci = i / ONE_MAX_NODES;
                if ((uint64_t)length > UINT64_MAX - first_spans[ci]) { free(first_spans); return -13; }
                first_spans[ci] += (uint64_t)length;
            }
        }
        if (covered != target_len) { free(first_spans); return -10; }
    } else {
        if (target_len > SIZE_MAX - surprise_total) { free(first_spans); return -7; }
        surprise_total += target_len;
    }

    size_t intermediate_total = 0u;
    size_t hierarchy_depth = enabled ? 1u : 0u;
    size_t level_count = segment_count;
    while (enabled && level_count > ONE_MAX_NODES) {
        level_count = (level_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        if (level_count > SIZE_MAX - intermediate_total) { free(first_spans); return -11; }
        intermediate_total += level_count;
        if (++hierarchy_depth > ONE_MAX_DEPTH) { free(first_spans); return -11; }
    }

    const size_t node_count = enabled ? (1u + surprise_count + intermediate_total + 1u) : 2u;
    if (node_count > ONE_MAX_NODES) { free(first_spans); return -12; }

    /* Acceptance semantics remain exactly the seed's deliberately loose guard. */
    size_t seed_cap = 0u;
    if (checked_cap(source_len, target_len, segment_count, intermediate_total, &seed_cap) != 0) {
        free(first_spans); return -13;
    }
    (void)seed_cap;

    size_t exact = 4u; /* ONE0 */
    if (exact_add_uv(&exact, ONE_MAX_NODES) != 0 || exact_add_uv(&exact, ONE_MAX_OUTPUT) != 0 ||
        exact_add_uv(&exact, ONE_MAX_WORK) != 0 || exact_add_uv(&exact, ONE_MAX_DEPTH) != 0 ||
        exact_add_uv(&exact, (uint64_t)node_count) != 0 || exact_add_surprise(&exact, source_len) != 0) {
        free(first_spans); return -13;
    }

    if (!enabled) {
        if (exact_add_surprise(&exact, target_len) != 0) { free(first_spans); return -13; }
    } else {
        if (exact_addz(&exact, exact_segment_surprises) != 0) { free(first_spans); return -13; }
        if (segment_count <= ONE_MAX_NODES) {
            if (exact_add_concat_head(&exact, (uint64_t)target_len, segment_count) != 0 ||
                exact_addz(&exact, exact_segment_refs) != 0 || exact_add_uv(&exact, 0u) != 0) {
                free(first_spans); return -13;
            }
        } else {
            /* First hierarchy level: ref sizes were fused into validation above. */
            if (exact_addz(&exact, exact_segment_refs) != 0) { free(first_spans); return -13; }
            for (size_t ci = 0; ci < first_count; ++ci) {
                size_t chunk = segment_count - ci * ONE_MAX_NODES;
                if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
                if (exact_add_concat_head(&exact, first_spans[ci], chunk) != 0 || exact_add_uv(&exact, 0u) != 0) {
                    free(first_spans); return -13;
                }
            }

            uint64_t *spans = first_spans;
            size_t nlevel = first_count;
            uint64_t level_node_start = 1u + (uint64_t)surprise_count;
            uint64_t next_node = level_node_start + (uint64_t)nlevel;
            while (nlevel > ONE_MAX_NODES) {
                const size_t next_count = (nlevel + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
                uint64_t *next_spans = (uint64_t *)calloc(next_count, sizeof(*next_spans));
                if (!next_spans) { free(spans); return -14; }
                size_t ni = 0u;
                for (size_t off = 0; off < nlevel; off += ONE_MAX_NODES) {
                    size_t chunk = nlevel - off;
                    if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
                    uint64_t declared = 0u;
                    if (exact_add_concat_head(&exact, 0u, 0u) != 0) {
                        free(next_spans); free(spans); return -13;
                    }
                    /* Undo placeholder head and add the real one after span sum. */
                    exact -= 1u + exact_uvlen(1u) + exact_uvlen(0u);
                    for (size_t j = 0; j < chunk; ++j) {
                        if (spans[off + j] > UINT64_MAX - declared) {
                            free(next_spans); free(spans); return -13;
                        }
                        declared += spans[off + j];
                    }
                    if (exact_add_concat_head(&exact, declared, chunk) != 0) {
                        free(next_spans); free(spans); return -13;
                    }
                    for (size_t j = 0; j < chunk; ++j) {
                        if (exact_add_ref(&exact, level_node_start + (uint64_t)(off + j), 0u, 0u, 0u) != 0) {
                            free(next_spans); free(spans); return -13;
                        }
                    }
                    if (exact_add_uv(&exact, 0u) != 0) { free(next_spans); free(spans); return -13; }
                    next_spans[ni++] = declared;
                }
                free(spans);
                spans = next_spans;
                level_node_start = next_node;
                next_node += (uint64_t)next_count;
                nlevel = next_count;
            }
            if (exact_add_concat_head(&exact, (uint64_t)target_len, nlevel) != 0) { free(spans); return -13; }
            for (size_t j = 0; j < nlevel; ++j) {
                if (exact_add_ref(&exact, level_node_start + (uint64_t)j, 0u, 0u, 0u) != 0) {
                    free(spans); return -13;
                }
            }
            if (exact_add_uv(&exact, 0u) != 0) { free(spans); return -13; }
            free(spans);
            first_spans = NULL;
        }
    }

    /* sorted roots: current, previous */
    if (exact_add_uv(&exact, 2u) != 0 || exact_add_blob(&exact, 7u) != 0 ||
        exact_add_ref(&exact, (uint64_t)(node_count - 1u), 0u, 0u, 0u) != 0 ||
        exact_add_uv(&exact, (uint64_t)target_len) != 0 || exact_addz(&exact, 32u) != 0 ||
        exact_add_blob(&exact, 8u) != 0 || exact_add_ref(&exact, 0u, 0u, 0u, 0u) != 0 ||
        exact_add_uv(&exact, (uint64_t)source_len) != 0 || exact_addz(&exact, 32u) != 0 ||
        exact > ONE_MAX_WIRE) {
        free(first_spans); return -13;
    }
    free(first_spans);

    uint8_t *raw = (uint8_t *)malloc(exact ? exact : 1u);
    if (!raw) return -14;
    one_out o = { raw, 0u, exact };
    static const uint8_t magic[4] = {'O','N','E','0'};
    int rc = 0;
#define TRY_EXACT(x) do { if ((rc = (x)) != 0) goto exact_fail; } while (0)
    TRY_EXACT(put_bytes(&o, magic, sizeof(magic)));
    TRY_EXACT(put_uvarint(&o, ONE_MAX_NODES));
    TRY_EXACT(put_uvarint(&o, ONE_MAX_OUTPUT));
    TRY_EXACT(put_uvarint(&o, ONE_MAX_WORK));
    TRY_EXACT(put_uvarint(&o, ONE_MAX_DEPTH));
    TRY_EXACT(put_uvarint(&o, (uint64_t)node_count));
    TRY_EXACT(put_surprise(&o, source, source_len));

    if (!enabled) {
        TRY_EXACT(put_surprise(&o, target, target_len));
    } else {
        for (size_t i = 0; i < segment_count; ++i)
            if (segments[i].kind == 1u)
                TRY_EXACT(put_surprise(&o, target + segments[i].start, segments[i].length));

        if (segment_count <= ONE_MAX_NODES) {
            TRY_EXACT(put_concat_from_segments(&o, segments, segment_count, (uint64_t)target_len));
        } else {
            one_level_ref *level = (one_level_ref *)malloc(segment_count * sizeof(*level));
            if (!level) { rc = -15; goto exact_fail; }
            uint64_t next_surprise_node = 1u;
            for (size_t i = 0; i < segment_count; ++i) {
                const one_g02_segment *s = &segments[i];
                if (s->kind == 0u) {
                    level[i].node = 0u; level[i].start = s->start;
                    level[i].wire_length = s->length; level[i].has_length = 1u;
                } else {
                    level[i].node = next_surprise_node++; level[i].start = 0u;
                    level[i].wire_length = 0u; level[i].has_length = 0u;
                }
                level[i].span = s->length;
            }
            uint64_t next_node = 1u + (uint64_t)surprise_count;
            size_t nlevel = segment_count;
            while (nlevel > ONE_MAX_NODES) {
                const size_t next_count = (nlevel + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
                one_level_ref *next = (one_level_ref *)malloc(next_count * sizeof(*next));
                if (!next) { free(level); rc = -15; goto exact_fail; }
                size_t ni = 0u;
                for (size_t off = 0; off < nlevel; off += ONE_MAX_NODES) {
                    size_t chunk = nlevel - off;
                    if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
                    uint64_t declared = 0u;
                    for (size_t j = 0; j < chunk; ++j) declared += level[off + j].span;
                    if ((rc = put_concat(&o, level + off, chunk, declared)) != 0) {
                        free(next); free(level); goto exact_fail;
                    }
                    next[ni].node = next_node++; next[ni].start = 0u;
                    next[ni].wire_length = 0u; next[ni].has_length = 0u;
                    next[ni].span = declared; ++ni;
                }
                free(level); level = next; nlevel = next_count;
            }
            if ((rc = put_concat(&o, level, nlevel, (uint64_t)target_len)) != 0) {
                free(level); goto exact_fail;
            }
            free(level);
        }
    }

    TRY_EXACT(put_uvarint(&o, 2u));
    TRY_EXACT(put_blob(&o, (const uint8_t *)"current", 7u));
    TRY_EXACT(put_ref(&o, (uint64_t)(node_count - 1u), 0u, 0u, 0u));
    TRY_EXACT(put_uvarint(&o, (uint64_t)target_len));
    TRY_EXACT(put_bytes(&o, current_digest, 32u));
    TRY_EXACT(put_blob(&o, (const uint8_t *)"previous", 8u));
    TRY_EXACT(put_ref(&o, 0u, 0u, 0u, 0u));
    TRY_EXACT(put_uvarint(&o, (uint64_t)source_len));
    TRY_EXACT(put_bytes(&o, previous_digest, 32u));

    if (o.len != exact) { rc = -21; goto exact_fail; }
    *out_data = raw;
    *out_len = o.len;
    *surprise_bytes = surprise_total;
    *allocated_bytes = exact;
    *hierarchy_depth_out = hierarchy_depth;
    *node_count_out = node_count;
    return 0;

exact_fail:
    free(raw);
    return rc ? rc : -20;
#undef TRY_EXACT
}

void one_g02_native_writer_exact_capacity_free(void *p) { free(p); }
