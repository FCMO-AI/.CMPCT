#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    uint32_t start;
    uint32_t length;
    uint8_t kind; /* 0=source Ref, 1=target Surprise */
} one_g02_segment;

typedef struct {
    uint64_t compared_target_bytes;
    uint64_t segments;
    uint64_t emitted_bytes;
    uint64_t transient_plan_bytes;
} one_g02_stream_stats;

static int is_ref_byte(const uint8_t *src, const uint8_t *dst, size_t i) {
    return i > 0 && dst[i] == src[i - 1];
}

static int put_u32le(uint8_t *out, size_t cap, size_t *pos, uint32_t v) {
    if (*pos + 4 > cap) return -1;
    out[(*pos)++] = (uint8_t)(v);
    out[(*pos)++] = (uint8_t)(v >> 8);
    out[(*pos)++] = (uint8_t)(v >> 16);
    out[(*pos)++] = (uint8_t)(v >> 24);
    return 0;
}

static int emit_record(uint8_t kind, uint32_t start, uint32_t len,
                       const uint8_t *dst, uint8_t *out, size_t cap, size_t *pos) {
    if (*pos + 9 > cap) return -1;
    out[(*pos)++] = kind;
    if (put_u32le(out, cap, pos, start) != 0 || put_u32le(out, cap, pos, len) != 0) return -1;
    if (kind) {
        if ((size_t)start + (size_t)len < (size_t)start || *pos + (size_t)len > cap) return -1;
        memcpy(out + *pos, dst + start, len);
        *pos += len;
    }
    return 0;
}

int one_g02_plan_then_stream(const uint8_t *src, const uint8_t *dst, size_t n,
                             one_g02_segment *plan, size_t plan_cap,
                             uint8_t *out, size_t out_cap,
                             one_g02_stream_stats *stats) {
    if (!src || !dst || !plan || !out || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    stats->emitted_bytes = 0;
    stats->transient_plan_bytes = 0;
    size_t i = 0;
    while (i < n) {
        int ref = is_ref_byte(src, dst, i);
        size_t begin = i++;
        while (i < n && is_ref_byte(src, dst, i) == ref) ++i;
        size_t len = i - begin;
        size_t idx = (size_t)stats->segments++;
        if (idx >= plan_cap || begin > UINT32_MAX || len > UINT32_MAX) return -2;
        plan[idx].kind = ref ? 0u : 1u;
        plan[idx].start = (uint32_t)(ref ? begin - 1 : begin);
        plan[idx].length = (uint32_t)len;
    }
    stats->transient_plan_bytes = stats->segments * (uint64_t)sizeof(one_g02_segment);
    size_t pos = 0;
    for (size_t j = 0; j < (size_t)stats->segments; ++j) {
        one_g02_segment s = plan[j];
        uint32_t payload_start = s.kind ? s.start : 0u;
        if (emit_record(s.kind, s.start, s.length, dst, out, out_cap, &pos) != 0) return -3;
        (void)payload_start;
    }
    stats->emitted_bytes = pos;
    return 0;
}

int one_g02_direct_stream(const uint8_t *src, const uint8_t *dst, size_t n,
                          uint8_t *out, size_t out_cap,
                          one_g02_stream_stats *stats) {
    if (!src || !dst || !out || !stats) return -1;
    stats->compared_target_bytes = n;
    stats->segments = 0;
    stats->emitted_bytes = 0;
    stats->transient_plan_bytes = 0;
    size_t pos = 0;
    size_t i = 0;
    while (i < n) {
        int ref = is_ref_byte(src, dst, i);
        size_t begin = i++;
        while (i < n && is_ref_byte(src, dst, i) == ref) ++i;
        size_t len = i - begin;
        if (begin > UINT32_MAX || len > UINT32_MAX) return -2;
        uint32_t start = (uint32_t)(ref ? begin - 1 : begin);
        if (emit_record(ref ? 0u : 1u, start, (uint32_t)len, dst, out, out_cap, &pos) != 0) return -3;
        stats->segments++;
    }
    stats->emitted_bytes = pos;
    return 0;
}
