#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

/* ONE-G0.2 encoder-discovery Builder.
 *
 * Full-span edge replay was retired by exact native evidence. This successor uses the
 * already-canonical ONE observation WINDOW as its block size. Every eligible Gear state is
 * summarized into a fixed block rightmost-minimum. Exact 4096-position edge queries combine
 * completed block summaries with at most two partial blocks, reconstructing only boundary
 * states from bounded raw-byte history + per-block checkpoints.
 *
 * No reader semantics live here; this is discovery scheduling only.
 */
typedef struct {
    uint64_t block_id;
    uint64_t min_value;
    uint64_t min_position;
    uint64_t checkpoint;
} one_g02_block_record;

typedef struct {
    uint64_t emitted, final_state, positions_considered, sparse_anchors;
    uint64_t queries, reconstructed_boundary_states, scanned_block_summaries;
    uint64_t reserved_state_bytes;
} one_g02_block_edge_result;

#define ONE_G02_ANCHOR_MASK ((uint64_t)1023)
#define ONE_G02_MIN_RUN ((size_t)8)
#define ONE_G02_INVALID_BLOCK UINT64_MAX

static int block_query(
    const uint8_t *raw, size_t raw_cap, const one_g02_block_record *records, size_t record_cap,
    const uint64_t gear[256], size_t window, size_t span, uint64_t end_position,
    one_g02_block_edge_result *out, uint64_t *trace, size_t trace_capacity,
    uint64_t *last_emitted
) {
    if (end_position + 1 < window + span - 1) return 0;
    uint64_t eligible_end = end_position + 1 - (uint64_t)window;
    if (eligible_end + 1 < (uint64_t)span) return 0;
    uint64_t eligible_start = eligible_end + 1 - (uint64_t)span;
    uint64_t start_position = eligible_start + (uint64_t)window - 1;
    uint64_t start_block = eligible_start / (uint64_t)window;
    uint64_t end_block = eligible_end / (uint64_t)window;
    uint64_t best = UINT64_MAX, best_position = 0;
    out->queries++;

    for (uint64_t bid = start_block; bid <= end_block; ++bid) {
        const one_g02_block_record *rec = &records[bid % record_cap];
        if (rec->block_id != bid) return -6;
        uint64_t block_start = (uint64_t)window - 1 + bid * (uint64_t)window;
        uint64_t block_end = block_start + (uint64_t)window - 1;
        uint64_t qstart = start_position > block_start ? start_position : block_start;
        uint64_t qend = end_position < block_end ? end_position : block_end;
        if (qstart == block_start && qend == block_end) {
            out->scanned_block_summaries++;
            if (rec->min_value <= best) { best = rec->min_value; best_position = rec->min_position; }
            continue;
        }
        uint64_t replay = rec->checkpoint;
        for (uint64_t pos = block_start; pos <= qend; ++pos) {
            replay = (replay << 1) + gear[raw[pos % raw_cap]];
            out->reconstructed_boundary_states++;
            if (pos >= qstart && replay <= best) { best = replay; best_position = pos; }
        }
    }
    if (best_position == *last_emitted) return 0;
    *last_emitted = best_position;
    if (trace) {
        if (out->emitted >= trace_capacity) return -4;
        trace[out->emitted] = best_position;
    }
    out->emitted++;
    return 0;
}

int one_g02_starvation_block_edge_kernel(
    const uint8_t *data, size_t length, const uint64_t gear[256], size_t window, size_t span,
    one_g02_block_edge_result *out, uint64_t *trace, size_t trace_capacity
) {
    if (!out || !gear || !window || !span || span % window != 0) return -1;
    *out = (one_g02_block_edge_result){0};
    if (!length) return 0;
    if (!data) return -1;

    size_t raw_cap = span + window - 1;
    size_t record_cap = span / window + 2;
    uint8_t *raw = (uint8_t *)malloc(raw_cap);
    one_g02_block_record *records = (one_g02_block_record *)malloc(record_cap * sizeof(*records));
    if (!raw || !records) { free(raw); free(records); return -2; }
    for (size_t i=0;i<record_cap;++i) records[i].block_id=ONE_G02_INVALID_BLOCK;
    out->reserved_state_bytes = (uint64_t)raw_cap
        + (uint64_t)(record_cap * sizeof(*records))
        + (uint64_t)(256 * sizeof(uint64_t));

    uint64_t state=0, last_sparse=UINT64_MAX, last_emitted=UINT64_MAX;
    int active=0; uint8_t run_value=data[0]; size_t run_length=0;

    for (size_t position=0; position<length; ++position) {
        uint8_t value=data[position];
        if (!run_length) { run_value=value; run_length=1; }
        else if (value==run_value) run_length++;
        else { run_value=value; run_length=1; }

        uint64_t before=state;
        state=(state<<1)+gear[value];
        if (position+1<window) continue;
        out->positions_considered++;
        int rd=run_length >= (window>ONE_G02_MIN_RUN?window:ONE_G02_MIN_RUN);
        int sparse=((state&ONE_G02_ANCHOR_MASK)==0)&&!rd;

        if (sparse && active) {
            int rc=block_query(raw,raw_cap,records,record_cap,gear,window,span,
                               (uint64_t)position-1,out,trace,trace_capacity,&last_emitted);
            if (rc) { free(raw); free(records); return rc; }
            active=0; last_emitted=UINT64_MAX;
        }

        raw[position % raw_cap]=value;
        uint64_t eligible=(uint64_t)(position+1-window);
        uint64_t bid=eligible/(uint64_t)window;
        uint64_t off=eligible%(uint64_t)window;
        one_g02_block_record *rec=&records[bid%record_cap];
        if (off==0) {
            rec->block_id=bid; rec->min_value=state; rec->min_position=(uint64_t)position; rec->checkpoint=before;
        } else {
            if (rec->block_id!=bid) { free(raw); free(records); return -5; }
            if (state<=rec->min_value) { rec->min_value=state; rec->min_position=(uint64_t)position; }
        }

        if (sparse) { out->sparse_anchors++; last_sparse=(uint64_t)position; continue; }
        if (rd) continue;
        uint64_t gap=last_sparse==UINT64_MAX?(uint64_t)(position+1-window):(uint64_t)position-last_sparse;
        if (gap>=(uint64_t)span && !active) {
            int rc=block_query(raw,raw_cap,records,record_cap,gear,window,span,
                               (uint64_t)position,out,trace,trace_capacity,&last_emitted);
            if (rc) { free(raw); free(records); return rc; }
            active=1;
        }
    }
    if (active) {
        int rc=block_query(raw,raw_cap,records,record_cap,gear,window,span,
                           (uint64_t)length-1,out,trace,trace_capacity,&last_emitted);
        if (rc) { free(raw); free(records); return rc; }
    }
    out->final_state=state;
    free(raw); free(records); return 0;
}
