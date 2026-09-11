#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    uint64_t offset;
    uint64_t length;
    uint8_t value;
} one_fill_cmd;

int one_apply_fill_schedule(
    uint8_t *sink,
    size_t sink_len,
    const one_fill_cmd *cmds,
    size_t count
) {
    if ((sink_len && !sink) || (count && !cmds)) return 1;
    for (size_t i = 0; i < count; ++i) {
        const uint64_t off = cmds[i].offset;
        const uint64_t len = cmds[i].length;
        if (off > sink_len || len > (uint64_t)(sink_len - (size_t)off)) return 2;
        if (len) memset(sink + (size_t)off, cmds[i].value, (size_t)len);
    }
    return 0;
}
