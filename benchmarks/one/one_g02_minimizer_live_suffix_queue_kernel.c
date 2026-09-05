#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/* ONE-G0.2 Builder: fuse suffix construction with its only future query epoch.
 *
 * Four raw Gear-state blocks are retained exactly as in the promoted offset-only
 * baseline.  Instead of materializing four dense suffix-argmin tables when each
 * block closes, this kernel waits until block q-4 is actually about to be queried.
 * At r=0, before slot q overwrites the old slot, it constructs one monotonic queue
 * over old offsets [1, block_size).  As r advances left-to-right, old offsets are
 * overwritten in exactly the same order that they expire from the suffix domain.
 * Thus one live uint16 offset queue is sufficient for the exact suffix candidate;
 * no source byte is reread and no reader-visible semantics change.
 */

typedef struct {
    uint64_t emitted;
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t live_queue_builds;
    uint64_t live_queue_pushes;
    uint64_t live_queue_pops_back;
    uint64_t live_queue_pops_front;
    uint64_t suffix_value_indirect_loads;
} one_g02_live_suffix_result;

static int emit_anchor(one_g02_live_suffix_result *out, uint64_t anchor,
                       uint64_t *trace, size_t cap, uint64_t *last) {
    if (anchor == *last) return 0;
    if (trace != NULL) {
        if (out->emitted >= cap) return -4;
        trace[out->emitted] = anchor;
    }
    *last = anchor;
    out->emitted += 1;
    return 0;
}

int one_g02_minimizer_live_suffix_queue_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256],
    size_t window, size_t minimizer_span, one_g02_live_suffix_result *out,
    uint64_t *trace, size_t trace_capacity
) {
    if (out == NULL || gear == NULL || window == 0 || minimizer_span == 0) return -1;
    if (minimizer_span % 4 != 0) return -3;
    const size_t block_size = minimizer_span / 4;
    if (block_size == 0 || block_size > UINT16_MAX) return -3;
    *out = (one_g02_live_suffix_result){0};
    if (length == 0) return 0;
    if (data == NULL) return -1;

    const int enabled = length >= minimizer_span + window;
    uint64_t *block_values = NULL;
    uint16_t *queue = NULL;
    if (enabled) {
        block_values = (uint64_t *)malloc(4 * block_size * sizeof(uint64_t));
        queue = (uint16_t *)malloc(block_size * sizeof(uint16_t));
        if (block_values == NULL || queue == NULL) {
            free(block_values); free(queue); return -2;
        }
        out->reserved_state_bytes =
            4 * block_size * sizeof(uint64_t) + block_size * sizeof(uint16_t) +
            4 * (sizeof(uint64_t) + sizeof(uint64_t) + sizeof(uint64_t)) +
            2 * sizeof(uint64_t);
    }

    uint64_t block_min_value[4] = {0,0,0,0};
    uint64_t block_min_position[4] = {0,0,0,0};
    uint64_t block_number[4] = {UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX};
    uint64_t state=0, prefix_value=0, prefix_position=0;
    uint64_t middle_value=0, middle_position=0, last_emitted=UINT64_MAX;
    uint64_t states_seen=0, q=0;
    size_t r=0, qhead=0, qtail=0;

    for (size_t position=0; position<length; ++position) {
        state = (state << 1) + gear[data[position]];
        if (position + 1 < window) continue;
        out->positions_considered += 1;
        if (!enabled) continue;

        const size_t slot = (size_t)(q & 3u);
        const size_t base = slot * block_size;
        if (r == 0) {
            /* Build exactly when this old block becomes queryable and before its
             * first raw state is overwritten by the new block sharing the slot. */
            qhead = qtail = 0;
            if (q >= 4) {
                const uint64_t old_block = q - 4;
                if (block_number[slot] != old_block) { free(block_values); free(queue); return -5; }
                for (size_t i=1; i<block_size; ++i) {
                    const uint64_t value = block_values[base+i];
                    out->derived_state_reads += 1;
                    while (qtail > qhead) {
                        const uint16_t back = queue[qtail-1];
                        out->derived_state_reads += 1;
                        if (block_values[base+back] < value) break;
                        qtail -= 1;
                        out->live_queue_pops_back += 1;
                    }
                    queue[qtail++] = (uint16_t)i;
                    out->live_queue_pushes += 1;
                }
                out->live_queue_builds += 1;
            }

            prefix_value = state;
            prefix_position = (uint64_t)position;
            if (q >= 3) {
                uint64_t b=q-3; size_t ms=(size_t)(b&3u);
                if (block_number[ms] != b) { free(block_values); free(queue); return -5; }
                middle_value=block_min_value[ms]; middle_position=block_min_position[ms];
                for (b=q-2; b<=q-1; ++b) {
                    ms=(size_t)(b&3u);
                    if (block_number[ms] != b) { free(block_values); free(queue); return -5; }
                    if (block_min_value[ms] <= middle_value) {
                        middle_value=block_min_value[ms]; middle_position=block_min_position[ms];
                    }
                }
            }
        } else if (state <= prefix_value) {
            prefix_value=state; prefix_position=(uint64_t)position;
        }

        if (states_seen + 1 >= minimizer_span) {
            uint64_t selected_value=middle_value, selected_position=middle_position;
            if (prefix_value <= selected_value) {
                selected_value=prefix_value; selected_position=prefix_position;
            }
            if (q >= 4 && r + 1 < block_size) {
                const size_t need = r + 1;
                while (qhead < qtail && queue[qhead] < need) {
                    qhead += 1; out->live_queue_pops_front += 1;
                }
                if (qhead >= qtail) { free(block_values); free(queue); return -6; }
                const uint16_t argmin=queue[qhead];
                const uint64_t old_value=block_values[base+argmin];
                out->suffix_value_indirect_loads += 1;
                if (old_value < selected_value) {
                    selected_value=old_value;
                    selected_position=(uint64_t)(window-1)+(q-4)*block_size+argmin;
                }
            }
            const int rc=emit_anchor(out,selected_position,trace,trace_capacity,&last_emitted);
            if (rc != 0) { free(block_values); free(queue); return rc; }
        }

        /* Safe after the suffix query: this is precisely the old offset that has
         * just expired from every future suffix domain. */
        block_values[base+r]=state;

        if (r + 1 == block_size) {
            block_min_value[slot]=prefix_value;
            block_min_position[slot]=prefix_position;
            block_number[slot]=q;
        }
        states_seen += 1;
        if (r + 1 == block_size) { r=0; q+=1; } else { r+=1; }
    }
    out->final_state=state;
    free(block_values); free(queue); return 0;
}
