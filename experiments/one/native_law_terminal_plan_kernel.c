#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    uint64_t offset;
    uint64_t length;
    uint64_t source_offset;
    uint8_t value;
    uint8_t kind;
} one_law_cmd;

enum {
    ONE_COPY = 0,
    ONE_FILL = 1,
    ONE_ADD8_CONST = 2,
    ONE_XOR_CONST = 3
};

int one_apply_law_terminal_schedule(
    uint8_t *sink, size_t sink_len,
    const uint8_t *source, size_t source_len,
    const one_law_cmd *commands, size_t command_count) {
    uint64_t cursor = 0;
    if ((sink_len && !sink) || (command_count && !commands)) return 1;
    for (size_t i = 0; i < command_count; ++i) {
        const one_law_cmd *c = &commands[i];
        if (c->offset != cursor) return 2;
        if (c->offset > sink_len || c->length > sink_len - c->offset) return 3;
        uint8_t *dst = sink + c->offset;
        if (c->kind == ONE_FILL) {
            memset(dst, c->value, (size_t)c->length);
        } else {
            if (c->source_offset > source_len || c->length > source_len - c->source_offset) return 4;
            if (c->length && !source) return 5;
            const uint8_t *src = source + c->source_offset;
            if (c->kind == ONE_COPY) {
                memcpy(dst, src, (size_t)c->length);
            } else if (c->kind == ONE_ADD8_CONST) {
                for (uint64_t j = 0; j < c->length; ++j) dst[j] = (uint8_t)(src[j] + c->value);
            } else if (c->kind == ONE_XOR_CONST) {
                for (uint64_t j = 0; j < c->length; ++j) dst[j] = (uint8_t)(src[j] ^ c->value);
            } else {
                return 6;
            }
        }
        cursor += c->length;
    }
    return cursor == sink_len ? 0 : 7;
}

/*
 * Bulk execution primitive for a validated periodic source view.
 *
 * This is not an ONE opcode and carries no discovery semantics.  The ONE reader has
 * already proven a Repeat relation and supplies the exact source period and phase.  The
 * kernel only performs bounded byte movement, using memcpy-sized chunks instead of one
 * Python command object per period.
 */
int one_copy_periodic(
    uint8_t *sink, size_t sink_len,
    const uint8_t *source, size_t source_len,
    size_t source_offset, size_t period, size_t phase) {
    if (sink_len && !sink) return 1;
    if (period == 0) return sink_len == 0 ? 0 : 2;
    if (!source) return 3;
    if (source_offset > source_len || period > source_len - source_offset) return 4;
    if (phase >= period) return 5;

    const uint8_t *basis = source + source_offset;
    size_t written = 0;
    size_t first = period - phase;
    if (first > sink_len) first = sink_len;
    if (first) {
        memcpy(sink, basis + phase, first);
        written = first;
    }
    while (sink_len - written >= period) {
        memcpy(sink + written, basis, period);
        written += period;
    }
    if (written < sink_len) {
        memcpy(sink + written, basis, sink_len - written);
    }
    return 0;
}
