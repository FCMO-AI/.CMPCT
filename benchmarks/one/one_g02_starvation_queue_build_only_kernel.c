#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct { uint64_t value; uint64_t position; } one_g02_qbo_entry;
typedef struct {
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t sparse_anchors;
    uint64_t rescue_active_positions;
    uint64_t activation_events;
    uint64_t replayed_history_bytes;
    uint64_t built_queue_entries;
    uint64_t peak_queue_entries;
    uint64_t build_checksum;
    uint64_t reserved_state_bytes;
} one_g02_qbo_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)

static void push(one_g02_qbo_entry *q, size_t span, size_t *head, size_t *count,
                 uint64_t signal, uint64_t position) {
    while (*count > 0) {
        size_t tail = (*head + *count - 1) % span;
        if (q[tail].value < signal) break;
        *count -= 1;
    }
    size_t slot = (*head + *count) % span;
    q[slot].value = signal;
    q[slot].position = position;
    *count += 1;
}

/* Exact activation replay + exact monotonic queue construction, but no queue maintenance
 * after activation. This is a causal timing arm only; it emits no nominations. */
int one_g02_starvation_queue_build_only_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256],
    size_t window, size_t span, one_g02_qbo_result *out
) {
    if (!out || !gear || window == 0 || span == 0) return -1;
    *out = (one_g02_qbo_result){0};
    if (length == 0) return 0;
    if (!data) return -1;
    uint8_t *history = (uint8_t *)malloc(span);
    one_g02_qbo_entry *queue = (one_g02_qbo_entry *)malloc(span * sizeof(*queue));
    if (!history || !queue) { free(history); free(queue); return -2; }
    out->reserved_state_bytes = (uint64_t)span + (uint64_t)(span * sizeof(*queue))
                              + (uint64_t)(256 * sizeof(uint64_t));
    size_t hcount=0, hnext=0, head=0, count=0;
    uint64_t hseed=0, state=0, last_sparse=UINT64_MAX;
    int active=0;
    uint8_t run_value=data[0]; size_t run_length=0;
    for (size_t position=0; position<length; ++position) {
        uint8_t value=data[position];
        if (run_length==0) { run_value=value; run_length=1; }
        else if (value==run_value) run_length++;
        else { run_value=value; run_length=1; }
        uint64_t before=state; state=(state<<1)+gear[value];
        if (position+1<window) continue;
        out->positions_considered++;
        if (hcount==0) hseed=before;
        else if (hcount==span) { uint8_t oldest=history[hnext]; hseed=(hseed<<1)+gear[oldest]; }
        history[hnext]=value; hnext=(hnext+1)%span; if (hcount<span) hcount++;
        int run_dominated=run_length >= (window>ONE_G02_MIN_RUN ? window : ONE_G02_MIN_RUN);
        int sparse=((state&ONE_G02_ANCHOR_MASK)==0) && !run_dominated;
        if (sparse) { out->sparse_anchors++; last_sparse=(uint64_t)position; active=0; continue; }
        uint64_t gap=last_sparse==UINT64_MAX ? (uint64_t)(position+1-window) : (uint64_t)position-last_sparse;
        if (run_dominated || gap<(uint64_t)span) continue;
        out->rescue_active_positions++;
        if (!active) {
            if (hcount<span) continue;
            head=0; count=0; uint64_t replay=hseed;
            uint64_t oldest_pos=(uint64_t)(position+1-hcount); size_t oldest_slot=hnext;
            for (size_t j=0; j<hcount; ++j) {
                uint8_t rv=history[(oldest_slot+j)%span]; replay=(replay<<1)+gear[rv];
                push(queue,span,&head,&count,replay,oldest_pos+(uint64_t)j);
            }
            out->replayed_history_bytes += hcount;
            out->built_queue_entries += hcount;
            if (count>out->peak_queue_entries) out->peak_queue_entries=count;
            if (count) out->build_checksum ^= queue[head].value ^ queue[head].position;
            out->activation_events++;
            if (replay!=state) { free(history); free(queue); return -3; }
            active=1;
        }
    }
    out->final_state=state; free(history); free(queue); return 0;
}
