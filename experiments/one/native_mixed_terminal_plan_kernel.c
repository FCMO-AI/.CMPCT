#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    uint64_t offset;
    uint64_t length;
    uint64_t source_offset;
    uint8_t value;
    uint8_t kind;
} one_mixed_cmd;

enum { ONE_COPY = 0, ONE_FILL = 1 };

int one_apply_mixed_terminal_schedule(
    uint8_t *sink, size_t sink_len,
    const uint8_t *source, size_t source_len,
    const one_mixed_cmd *commands, size_t command_count) {
    uint64_t cursor = 0;
    if ((sink_len && !sink) || (command_count && !commands)) return 1;
    for (size_t i = 0; i < command_count; ++i) {
        const one_mixed_cmd *c = &commands[i];
        if (c->offset != cursor) return 2;
        if (c->offset > sink_len || c->length > sink_len - c->offset) return 3;
        if (c->kind == ONE_COPY) {
            if (c->source_offset > source_len || c->length > source_len - c->source_offset) return 4;
            if (c->length && !source) return 5;
            memcpy(sink + c->offset, source + c->source_offset, (size_t)c->length);
        } else if (c->kind == ONE_FILL) {
            memset(sink + c->offset, c->value, (size_t)c->length);
        } else {
            return 6;
        }
        cursor += c->length;
    }
    return cursor == sink_len ? 0 : 7;
}
