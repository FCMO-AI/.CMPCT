#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#define ONE_MAX_NODES 4096u
#define ONE_MAX_OUTPUT (64u * 1024u * 1024u)
#define ONE_MAX_WORK (256u * 1024u * 1024u)
#define ONE_MAX_DEPTH 64u
#define ONE_MAX_WIRE (128u * 1024u * 1024u)

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind; /* 0=source Ref, 1=target Surprise */
} one_g02_segment;

typedef struct {
    uint64_t node;
    uint64_t start;
    uint64_t wire_length;
    uint64_t span;
    uint8_t has_length;
} one_size_ref;

static int addz(size_t *v, size_t n) {
    if (!v || n > SIZE_MAX - *v) return -1;
    *v += n;
    return 0;
}

static size_t uvlen(uint64_t v) {
    size_t n = 1u;
    while (v >= 0x80u) { v >>= 7; ++n; }
    return n;
}

static int add_uv(size_t *n, uint64_t v) { return addz(n, uvlen(v)); }
static int add_blob(size_t *n, size_t len) {
    if (add_uv(n, (uint64_t)len) != 0) return -1;
    return addz(n, len);
}
static int add_ref(size_t *n, uint64_t node, uint64_t start,
                   uint8_t has_length, uint64_t wire_length) {
    if (add_uv(n, node) != 0 || add_uv(n, start) != 0) return -1;
    return add_uv(n, has_length ? wire_length + 1u : 0u);
}
static int add_surprise(size_t *n, size_t len) {
    if (addz(n, 1u) != 0 || add_uv(n, 0u) != 0) return -1;
    return add_blob(n, len);
}
static int add_concat(size_t *n, const one_size_ref *refs, size_t count, uint64_t declared) {
    if (addz(n, 1u) != 0 || add_uv(n, declared + 1u) != 0 || add_uv(n, (uint64_t)count) != 0)
        return -1;
    for (size_t i = 0; i < count; ++i) {
        if (add_ref(n, refs[i].node, refs[i].start, refs[i].has_length, refs[i].wire_length) != 0)
            return -1;
    }
    return add_uv(n, 0u); /* empty concat Surprise blob */
}

static int add_concat_from_segments(size_t *n, const one_g02_segment *segments,
                                    size_t count, uint64_t declared) {
    if (addz(n, 1u) != 0 || add_uv(n, declared + 1u) != 0 || add_uv(n, (uint64_t)count) != 0)
        return -1;
    uint64_t next_surprise_node = 1u;
    for (size_t i = 0; i < count; ++i) {
        const one_g02_segment *s = &segments[i];
        if (s->kind == 0u) {
            if (add_ref(n, 0u, (uint64_t)s->start, 1u, (uint64_t)s->length) != 0) return -1;
        } else {
            if (add_ref(n, next_surprise_node++, 0u, 0u, 0u) != 0) return -1;
        }
    }
    return add_uv(n, 0u);
}

/* Mirror the seed writer's current conservative acceptance boundary exactly.
 * Exact sizing may reduce allocation after acceptance, but must not silently
 * broaden the writer's accepted domain in this experiment. */
static int seed_checked_cap(size_t source_len, size_t target_len, size_t segments,
                            size_t intermediate_nodes) {
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -1;
    if (segments > (SIZE_MAX - 4096u) / 64u) return -1;
    size_t cap = 4096u + segments * 64u;
    if (intermediate_nodes > (SIZE_MAX - cap) / 64u) return -1;
    cap += intermediate_nodes * 64u;
    if (source_len > SIZE_MAX - cap) return -1;
    cap += source_len;
    if (target_len > SIZE_MAX - cap) return -1;
    cap += target_len;
    return cap <= ONE_MAX_WIRE ? 0 : -1;
}

/*
 * Metadata-only exact ONE0 wire sizing oracle for the shared native writer.
 * It deliberately never reads source/target payload bytes. Return codes mirror
 * the writer's validation classes where practical; accepted/rejected domain is
 * intentionally held to the seed writer during this falsifier.
 */
int one_g02_exact_wire_size(
    size_t source_len, size_t target_len,
    const one_g02_segment *segments, size_t segment_count,
    int enabled, size_t *wire_len_out,
    size_t *surprise_bytes_out, size_t *hierarchy_depth_out,
    size_t *node_count_out) {

    if (!wire_len_out || !surprise_bytes_out || !hierarchy_depth_out || !node_count_out) return -1;
    *wire_len_out = *surprise_bytes_out = *hierarchy_depth_out = *node_count_out = 0u;
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -2;
    if ((enabled && (!segments || segment_count == 0u)) || (!enabled && segment_count != 0u)) return -3;
    if (segment_count > target_len) return -3;

    size_t surprise_count = 0u, surprise_total = source_len, covered = 0u;
    if (enabled) {
        for (size_t i = 0; i < segment_count; ++i) {
            const size_t start = (size_t)segments[i].start;
            const size_t length = (size_t)segments[i].length;
            if (length == 0u) return -4;
            if (segments[i].kind == 0u) {
                if (start > source_len || length > source_len - start) return -5;
            } else if (segments[i].kind == 1u) {
                if (start > target_len || length > target_len - start) return -6;
                ++surprise_count;
                if (length > SIZE_MAX - surprise_total) return -7;
                surprise_total += length;
            } else return -8;
            if (length > target_len - covered) return -9;
            covered += length;
        }
        if (covered != target_len) return -10;
    } else {
        if (target_len > SIZE_MAX - surprise_total) return -7;
        surprise_total += target_len;
    }

    size_t intermediate_total = 0u;
    size_t hierarchy_depth = enabled ? 1u : 0u;
    size_t level_count = segment_count;
    while (enabled && level_count > ONE_MAX_NODES) {
        level_count = (level_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        if (level_count > SIZE_MAX - intermediate_total) return -11;
        intermediate_total += level_count;
        if (++hierarchy_depth > ONE_MAX_DEPTH) return -11;
    }
    const size_t node_count = enabled ? (1u + surprise_count + intermediate_total + 1u) : 2u;
    if (node_count > ONE_MAX_NODES) return -12;
    if (seed_checked_cap(source_len, target_len, segment_count, intermediate_total) != 0) return -13;

    size_t n = 4u; /* ONE0 */
    if (add_uv(&n, ONE_MAX_NODES) != 0 || add_uv(&n, ONE_MAX_OUTPUT) != 0 ||
        add_uv(&n, ONE_MAX_WORK) != 0 || add_uv(&n, ONE_MAX_DEPTH) != 0 ||
        add_uv(&n, (uint64_t)node_count) != 0 || add_surprise(&n, source_len) != 0) return -13;

    if (!enabled) {
        if (add_surprise(&n, target_len) != 0) return -13;
    } else {
        for (size_t i = 0; i < segment_count; ++i)
            if (segments[i].kind == 1u && add_surprise(&n, segments[i].length) != 0) return -13;

        if (segment_count <= ONE_MAX_NODES) {
            if (add_concat_from_segments(&n, segments, segment_count, (uint64_t)target_len) != 0)
                return -13;
        } else {
            /* Hierarchy path mirrors the seed's generic temporary structure. */
            one_size_ref *level = (one_size_ref *)malloc(segment_count * sizeof(*level));
            if (!level) return -14;
            uint64_t next_surprise = 1u;
            for (size_t i = 0; i < segment_count; ++i) {
                const one_g02_segment *s = &segments[i];
                level[i].node = s->kind == 0u ? 0u : next_surprise++;
                level[i].start = s->kind == 0u ? s->start : 0u;
                level[i].wire_length = s->kind == 0u ? s->length : 0u;
                level[i].has_length = s->kind == 0u ? 1u : 0u;
                level[i].span = s->length;
            }
            uint64_t next_node = 1u + (uint64_t)surprise_count;
            size_t nlevel = segment_count;
            while (nlevel > ONE_MAX_NODES) {
                const size_t next_count = (nlevel + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
                one_size_ref *next = (one_size_ref *)malloc(next_count * sizeof(*next));
                if (!next) { free(level); return -14; }
                size_t ni = 0u;
                for (size_t off = 0; off < nlevel; off += ONE_MAX_NODES) {
                    size_t chunk = nlevel - off;
                    if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
                    uint64_t declared = 0u;
                    for (size_t j = 0; j < chunk; ++j) declared += level[off + j].span;
                    if (add_concat(&n, level + off, chunk, declared) != 0) {
                        free(next); free(level); return -13;
                    }
                    next[ni].node = next_node++;
                    next[ni].start = 0u; next[ni].wire_length = 0u; next[ni].has_length = 0u;
                    next[ni].span = declared; ++ni;
                }
                free(level); level = next; nlevel = next_count;
            }
            if (add_concat(&n, level, nlevel, (uint64_t)target_len) != 0) { free(level); return -13; }
            free(level);
        }
    }

    /* sorted roots: current, previous */
    if (add_uv(&n, 2u) != 0 || add_blob(&n, 7u) != 0 ||
        add_ref(&n, (uint64_t)(node_count - 1u), 0u, 0u, 0u) != 0 ||
        add_uv(&n, (uint64_t)target_len) != 0 || addz(&n, 32u) != 0 ||
        add_blob(&n, 8u) != 0 || add_ref(&n, 0u, 0u, 0u, 0u) != 0 ||
        add_uv(&n, (uint64_t)source_len) != 0 || addz(&n, 32u) != 0) return -13;
    if (n > ONE_MAX_WIRE) return -13;

    *wire_len_out = n;
    *surprise_bytes_out = surprise_total;
    *hierarchy_depth_out = hierarchy_depth;
    *node_count_out = node_count;
    return 0;
}
