#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

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
    uint64_t wire_length; /* ignored when has_length==0 */
    uint64_t span;
    uint8_t has_length;
} one_level_ref;

typedef struct {
    uint8_t *data;
    size_t len;
    size_t cap;
} one_out;

static int put_byte(one_out *o, uint8_t v) {
    if (!o || o->len >= o->cap) return -20;
    o->data[o->len++] = v;
    return 0;
}

static int put_bytes(one_out *o, const uint8_t *p, size_t n) {
    if (!o || (!p && n) || n > o->cap - o->len) return -20;
    if (n) memcpy(o->data + o->len, p, n);
    o->len += n;
    return 0;
}

static int put_uvarint(one_out *o, uint64_t v) {
    do {
        uint8_t b = (uint8_t)(v & 0x7fu);
        v >>= 7;
        if (v) b |= 0x80u;
        if (put_byte(o, b) != 0) return -20;
    } while (v);
    return 0;
}

static int put_blob(one_out *o, const uint8_t *p, size_t n) {
    if (put_uvarint(o, (uint64_t)n) != 0) return -20;
    return put_bytes(o, p, n);
}

static int put_ref(one_out *o, uint64_t node, uint64_t start,
                   uint8_t has_length, uint64_t wire_length) {
    if (put_uvarint(o, node) != 0) return -20;
    if (put_uvarint(o, start) != 0) return -20;
    return put_uvarint(o, has_length ? wire_length + 1u : 0u);
}

static int put_surprise(one_out *o, const uint8_t *p, size_t n) {
    if (put_byte(o, 0u) != 0) return -20; /* surprise */
    if (put_uvarint(o, 0u) != 0) return -20; /* no declared length */
    return put_blob(o, p, n);
}

static int put_concat(one_out *o, const one_level_ref *refs, size_t count, uint64_t declared) {
    if (put_byte(o, 1u) != 0) return -20; /* concat */
    if (put_uvarint(o, declared + 1u) != 0) return -20;
    if (put_uvarint(o, (uint64_t)count) != 0) return -20;
    for (size_t i = 0; i < count; ++i) {
        if (put_ref(o, refs[i].node, refs[i].start, refs[i].has_length, refs[i].wire_length) != 0)
            return -20;
    }
    return put_uvarint(o, 0u); /* empty concat Surprise blob */
}

static int checked_cap(size_t source_len, size_t target_len, size_t segments,
                       size_t intermediate_nodes, size_t *cap_out) {
    if (!cap_out) return -1;
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -2;
    if (segments > (SIZE_MAX - 4096u) / 64u) return -2;
    size_t cap = 4096u + segments * 64u;
    if (intermediate_nodes > (SIZE_MAX - cap) / 64u) return -2;
    cap += intermediate_nodes * 64u;
    if (source_len > SIZE_MAX - cap) return -2;
    cap += source_len;
    if (target_len > SIZE_MAX - cap) return -2;
    cap += target_len;
    if (cap > ONE_MAX_WIRE) return -2;
    *cap_out = cap;
    return 0;
}

/*
 * Return 0 on success. The caller owns *out_data and must release it with
 * one_g02_native_writer_free(). Digests are raw SHA-256 bytes.
 */
int one_g02_native_writer(
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
    *out_len = *surprise_bytes = *allocated_bytes = *hierarchy_depth_out = *node_count_out = 0;
    if (source_len > ONE_MAX_OUTPUT || target_len > ONE_MAX_OUTPUT) return -2;
    if ((enabled && (!segments || segment_count == 0)) || (!enabled && segment_count != 0)) return -3;
    if (segment_count > target_len) return -3;

    size_t surprise_count = 0;
    size_t covered = 0;
    size_t surprise_total = source_len;
    if (enabled) {
        for (size_t i = 0; i < segment_count; ++i) {
            const size_t start = (size_t)segments[i].start;
            const size_t length = (size_t)segments[i].length;
            if (length == 0) return -4;
            if (segments[i].kind == 0u) {
                if (start > source_len || length > source_len - start) return -5;
            } else if (segments[i].kind == 1u) {
                if (start > target_len || length > target_len - start) return -6;
                ++surprise_count;
                if (length > SIZE_MAX - surprise_total) return -7;
                surprise_total += length;
            } else {
                return -8;
            }
            if (length > target_len - covered) return -9;
            covered += length;
        }
        if (covered != target_len) return -10;
    } else {
        if (target_len > SIZE_MAX - surprise_total) return -7;
        surprise_total += target_len;
    }

    size_t intermediate_total = 0;
    size_t hierarchy_depth = enabled ? 1u : 0u;
    size_t level_count = segment_count;
    while (enabled && level_count > ONE_MAX_NODES) {
        level_count = (level_count + ONE_MAX_NODES - 1u) / ONE_MAX_NODES;
        if (level_count > SIZE_MAX - intermediate_total) return -11;
        intermediate_total += level_count;
        if (++hierarchy_depth > ONE_MAX_DEPTH) return -11;
    }

    size_t node_count = enabled ? (1u + surprise_count + intermediate_total + 1u) : 2u;
    if (node_count > ONE_MAX_NODES) return -12;

    size_t cap = 0;
    if (checked_cap(source_len, target_len, segment_count, intermediate_total, &cap) != 0) return -13;
    uint8_t *raw = (uint8_t *)malloc(cap ? cap : 1u);
    if (!raw) return -14;
    one_out o = { raw, 0u, cap };
    static const uint8_t magic[4] = {'O','N','E','0'};
    int rc = 0;
#define TRY(x) do { if ((rc = (x)) != 0) goto fail; } while (0)
    TRY(put_bytes(&o, magic, sizeof(magic)));
    TRY(put_uvarint(&o, ONE_MAX_NODES));
    TRY(put_uvarint(&o, ONE_MAX_OUTPUT));
    TRY(put_uvarint(&o, ONE_MAX_WORK));
    TRY(put_uvarint(&o, ONE_MAX_DEPTH));
    TRY(put_uvarint(&o, (uint64_t)node_count));
    TRY(put_surprise(&o, source, source_len));

    if (!enabled) {
        TRY(put_surprise(&o, target, target_len));
    } else {
        for (size_t i = 0; i < segment_count; ++i) {
            if (segments[i].kind == 1u) {
                TRY(put_surprise(&o, target + segments[i].start, segments[i].length));
            }
        }

        one_level_ref *level = (one_level_ref *)malloc(segment_count * sizeof(*level));
        if (!level) { rc = -15; goto fail; }
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
            if (!next) { free(level); rc = -15; goto fail; }
            size_t ni = 0;
            for (size_t off = 0; off < nlevel; off += ONE_MAX_NODES) {
                size_t chunk = nlevel - off;
                if (chunk > ONE_MAX_NODES) chunk = ONE_MAX_NODES;
                uint64_t declared = 0u;
                for (size_t j = 0; j < chunk; ++j) declared += level[off + j].span;
                TRY(put_concat(&o, level + off, chunk, declared));
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
        TRY(put_concat(&o, level, nlevel, (uint64_t)target_len));
        free(level);
    }

    /* sorted roots: current, previous */
    TRY(put_uvarint(&o, 2u));
    TRY(put_blob(&o, (const uint8_t *)"current", 7u));
    TRY(put_ref(&o, (uint64_t)(node_count - 1u), 0u, 0u, 0u));
    TRY(put_uvarint(&o, (uint64_t)target_len));
    TRY(put_bytes(&o, current_digest, 32u));
    TRY(put_blob(&o, (const uint8_t *)"previous", 8u));
    TRY(put_ref(&o, 0u, 0u, 0u, 0u));
    TRY(put_uvarint(&o, (uint64_t)source_len));
    TRY(put_bytes(&o, previous_digest, 32u));

    *out_data = raw;
    *out_len = o.len;
    *surprise_bytes = surprise_total;
    *allocated_bytes = cap;
    *hierarchy_depth_out = hierarchy_depth;
    *node_count_out = node_count;
    return 0;

fail:
    free(raw);
    return rc ? rc : -20;
#undef TRY
}

void one_g02_native_writer_free(void *p) { free(p); }
