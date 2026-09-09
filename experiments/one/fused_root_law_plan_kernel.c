#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    const uint8_t *src;
    size_t dst;
    size_t len;
    uint8_t value;
    uint8_t kind; /* 0 copy, 1 xor-constant, 2 add8-constant */
} one_root_cmd;

int one_execute_root_law_plan(uint8_t *dst, size_t dst_len,
                              const one_root_cmd *cmds, size_t cmd_count) {
    if ((!dst && dst_len) || (!cmds && cmd_count)) return 2;
    for (size_t c = 0; c < cmd_count; ++c) {
        const one_root_cmd *cmd = &cmds[c];
        if ((!cmd->src && cmd->len) || cmd->dst > dst_len || cmd->len > dst_len - cmd->dst)
            return 3;
        uint8_t *out = dst + cmd->dst;
        if (cmd->kind == 0) {
            if (cmd->len) memcpy(out, cmd->src, cmd->len);
        } else if (cmd->kind == 1) {
            for (size_t i = 0; i < cmd->len; ++i) out[i] = (uint8_t)(cmd->src[i] ^ cmd->value);
        } else if (cmd->kind == 2) {
            for (size_t i = 0; i < cmd->len; ++i) out[i] = (uint8_t)(cmd->src[i] + cmd->value);
        } else {
            return 4;
        }
    }
    return 0;
}
