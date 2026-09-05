#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct { uint64_t value; uint64_t position; } one_g02_lb_entry;
typedef struct {
    uint64_t emitted, final_state, positions_considered, sparse_anchors;
    uint64_t rescue_active_positions, replayed_history_bytes, peak_queue_entries;
    uint64_t reserved_state_bytes;
} one_g02_lb_result;
#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)

/* During activation construction head is provably zero and no expiry occurs. Therefore the
 * queue cannot wrap: generic modulo-ring addressing is unnecessary until construction ends. */
static inline void build_push_linear(one_g02_lb_entry *q, size_t *count,
                                     uint64_t signal, uint64_t position) {
    while (*count > 0 && q[*count - 1].value >= signal) *count -= 1;
    q[*count].value = signal; q[*count].position = position; *count += 1;
}
static inline void active_push(one_g02_lb_entry *q, size_t span, size_t *head, size_t *count,
                               uint64_t signal, uint64_t position) {
    while (*count > 0) {
        size_t tail=(*head + *count - 1) % span;
        if (q[tail].value < signal) break;
        *count -= 1;
    }
    size_t slot=(*head + *count) % span;
    q[slot].value=signal; q[slot].position=position; *count += 1;
}

int one_g02_starvation_linear_build_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256], size_t window, size_t span,
    one_g02_lb_result *out, uint64_t *trace, size_t trace_capacity
) {
    if (!out || !gear || !window || !span) return -1; *out=(one_g02_lb_result){0};
    if (!length) return 0; if (!data) return -1;
    uint8_t *history=(uint8_t*)malloc(span); one_g02_lb_entry *q=(one_g02_lb_entry*)malloc(span*sizeof(*q));
    if (!history || !q) { free(history); free(q); return -2; }
    out->reserved_state_bytes=(uint64_t)span+(uint64_t)(span*sizeof(*q))+(uint64_t)(256*sizeof(uint64_t));
    size_t hc=0,hn=0,head=0,count=0; uint64_t hseed=0,state=0,last_sparse=UINT64_MAX,last_emit=UINT64_MAX;
    int active=0; uint8_t run_value=data[0]; size_t run_length=0;
    for (size_t position=0; position<length; ++position) {
        uint8_t value=data[position];
        if (!run_length) { run_value=value; run_length=1; } else if (value==run_value) run_length++; else { run_value=value; run_length=1; }
        uint64_t before=state; state=(state<<1)+gear[value]; if (position+1<window) continue; out->positions_considered++;
        if (!hc) hseed=before; else if (hc==span) { uint8_t oldest=history[hn]; hseed=(hseed<<1)+gear[oldest]; }
        history[hn]=value; hn=(hn+1)%span; if (hc<span) hc++;
        int rd=run_length >= (window>ONE_G02_MIN_RUN?window:ONE_G02_MIN_RUN);
        int sparse=((state&ONE_G02_ANCHOR_MASK)==0)&&!rd;
        if (sparse) { out->sparse_anchors++; last_sparse=(uint64_t)position; active=0; head=0; count=0; last_emit=UINT64_MAX; continue; }
        uint64_t gap=last_sparse==UINT64_MAX?(uint64_t)(position+1-window):(uint64_t)position-last_sparse;
        if (rd || gap<(uint64_t)span) continue; out->rescue_active_positions++;
        if (!active) {
            if (hc<span) continue; head=0; count=0; uint64_t replay=hseed; uint64_t oldest_pos=(uint64_t)(position+1-hc); size_t oldest_slot=hn;
            for (size_t j=0;j<hc;++j) { uint8_t rv=history[(oldest_slot+j)%span]; replay=(replay<<1)+gear[rv]; build_push_linear(q,&count,replay,oldest_pos+(uint64_t)j); }
            out->replayed_history_bytes += hc; if (replay!=state) { free(history); free(q); return -3; } active=1;
        } else {
            uint64_t first_valid=(uint64_t)(position+1-span);
            while (count && q[head].position<first_valid) { head=(head+1)%span; count--; }
            active_push(q,span,&head,&count,state,(uint64_t)position);
        }
        if (count>out->peak_queue_entries) out->peak_queue_entries=count; if (!count) continue;
        uint64_t anchor=q[head].position; if (anchor==last_emit) continue; last_emit=anchor;
        if (trace) { if (out->emitted>=trace_capacity) { free(history); free(q); return -4; } trace[out->emitted]=anchor; }
        out->emitted++;
    }
    out->final_state=state; free(history); free(q); return 0;
}
