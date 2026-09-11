#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/* ONE-G0.2 Builder: exact 4096-span rightmost-min queue with structure-of-arrays
 * storage. Values remain u64. Positions are stored modulo 8192 in u16; because an entry is
 * expired at age >= span and span <=4096, modulo 8192 uniquely determines every live age.
 * Absolute emitted positions are reconstructed as current_position - modular_age.
 */
typedef struct {
    uint64_t emitted, final_state, positions_considered, sparse_anchors;
    uint64_t rescue_active_positions, replayed_history_bytes, peak_queue_entries;
    uint64_t reserved_state_bytes;
} one_g02_cq_result;
#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)
#define ONE_G02_POS_MOD ((uint64_t)8192)
#define ONE_G02_POS_MASK ((uint64_t)8191)

static inline uint64_t age_from_mod(uint64_t current, uint16_t stored) {
    return ((current & ONE_G02_POS_MASK) - (uint64_t)stored) & ONE_G02_POS_MASK;
}
static inline void build_push(uint64_t *values, uint16_t *positions, size_t *count,
                              uint64_t signal, uint64_t position) {
    while (*count > 0 && values[*count - 1] >= signal) *count -= 1;
    values[*count]=signal; positions[*count]=(uint16_t)(position & ONE_G02_POS_MASK); (*count)++;
}
static inline void active_push(uint64_t *values, uint16_t *positions, size_t span,
                               size_t *head, size_t *count, uint64_t signal, uint64_t position) {
    while (*count > 0) {
        size_t tail=(*head + *count - 1) % span;
        if (values[tail] < signal) break;
        (*count)--;
    }
    size_t slot=(*head + *count) % span;
    values[slot]=signal; positions[slot]=(uint16_t)(position & ONE_G02_POS_MASK); (*count)++;
}

int one_g02_starvation_compact_queue_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256], size_t window, size_t span,
    one_g02_cq_result *out, uint64_t *trace, size_t trace_capacity
) {
    if (!out || !gear || !window || !span || span > 4096) return -1;
    *out=(one_g02_cq_result){0}; if (!length) return 0; if (!data) return -1;
    uint8_t *history=(uint8_t*)malloc(span);
    uint64_t *qvalues=(uint64_t*)malloc(span*sizeof(uint64_t));
    uint16_t *qpositions=(uint16_t*)malloc(span*sizeof(uint16_t));
    if (!history || !qvalues || !qpositions) { free(history); free(qvalues); free(qpositions); return -2; }
    out->reserved_state_bytes=(uint64_t)span + (uint64_t)(span*sizeof(uint64_t))
      + (uint64_t)(span*sizeof(uint16_t)) + (uint64_t)(256*sizeof(uint64_t));
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
            for (size_t j=0;j<hc;++j) { uint8_t rv=history[(oldest_slot+j)%span]; replay=(replay<<1)+gear[rv]; build_push(qvalues,qpositions,&count,replay,oldest_pos+(uint64_t)j); }
            out->replayed_history_bytes += hc; if (replay!=state) { free(history); free(qvalues); free(qpositions); return -3; } active=1;
        } else {
            while (count && age_from_mod((uint64_t)position,qpositions[head]) >= (uint64_t)span) { head=(head+1)%span; count--; }
            active_push(qvalues,qpositions,span,&head,&count,state,(uint64_t)position);
        }
        if (count>out->peak_queue_entries) out->peak_queue_entries=count; if (!count) continue;
        uint64_t age=age_from_mod((uint64_t)position,qpositions[head]);
        if (age >= (uint64_t)span) { free(history); free(qvalues); free(qpositions); return -5; }
        uint64_t anchor=(uint64_t)position-age; if (anchor==last_emit) continue; last_emit=anchor;
        if (trace) { if (out->emitted>=trace_capacity) { free(history); free(qvalues); free(qpositions); return -4; } trace[out->emitted]=anchor; }
        out->emitted++;
    }
    out->final_state=state; free(history); free(qvalues); free(qpositions); return 0;
}
