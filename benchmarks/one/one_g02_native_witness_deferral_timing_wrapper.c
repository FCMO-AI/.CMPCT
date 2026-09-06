#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t cross_auditions, cross_witnesses, nominations;
    uint64_t local_peak_entries, global_peak_entries, global_capacity_entries;
    uint64_t verification_read_bytes, extension_read_bytes, anchors_consumed;
} one_g02_witness_consumer_result;

typedef struct {
    uint64_t samples, zero_shift_matches, coverage_compared_bytes, best_hits;
    int64_t best_shift;
    uint64_t proof_attempts, exact_proofs, proof_compared_bytes, strata_with_support;
} one_g02_safe_result;

typedef struct {
    double baseline_ns_per_call;
    double candidate_ns_per_call;
    int baseline_dispatch_path;
    int candidate_dispatch_path;
    int baseline_final_law;
    int candidate_final_law;
    one_g02_witness_consumer_result baseline_consumer;
    one_g02_witness_consumer_result candidate_consumer;
    one_g02_safe_result baseline_safe;
    one_g02_safe_result candidate_safe;
} one_g02_witness_timing_result;

extern int one_g02_native_witness_deferral_consume(
    const uint8_t *,size_t,size_t,const uint64_t[256],const uint64_t *,size_t,int,
    one_g02_witness_consumer_result *);
extern int one_g02_shift_relation_safe_dispatch(
    const uint8_t *,const uint8_t *,size_t,one_g02_safe_result *);

static uint64_t now_ns(void){
    struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);
    return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}

static int arm(const uint8_t *data,size_t length,size_t boundary,const uint64_t gear[256],
    const uint64_t *anchors,size_t anchor_count,int witness_only,
    one_g02_witness_consumer_result *cr,one_g02_safe_result *sr,int *path,int *law){
    int rc=one_g02_native_witness_deferral_consume(data,length,boundary,gear,anchors,anchor_count,witness_only,cr);
    if(rc)return rc;
    *path=-1;*law=0;*sr=(one_g02_safe_result){0};
    if(cr->nominations){
        size_t rel=boundary < length-boundary ? boundary : length-boundary;
        *path=one_g02_shift_relation_safe_dispatch(data,data+boundary,rel,sr);
        if(*path<0)return -20+*path;
        *law=sr->exact_proofs>=4;
    }
    return 0;
}

int one_g02_native_witness_deferral_measure(
    const uint8_t *data,size_t length,size_t boundary,const uint64_t gear[256],
    const uint64_t *anchors,size_t anchor_count,size_t batch,one_g02_witness_timing_result *out){
    if(!out||!data||!gear||!batch||boundary>length)return -1;
    one_g02_witness_consumer_result bc={0},cc={0};one_g02_safe_result bs={0},cs={0};int bp=-1,cp=-1,bl=0,cl=0;
    if(arm(data,length,boundary,gear,anchors,anchor_count,0,&bc,&bs,&bp,&bl)||
       arm(data,length,boundary,gear,anchors,anchor_count,1,&cc,&cs,&cp,&cl))return -2;
    uint64_t t,b1,b2,c1,c2;
    t=now_ns();for(size_t i=0;i<batch;++i)if(arm(data,length,boundary,gear,anchors,anchor_count,0,&bc,&bs,&bp,&bl))return -3;b1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)if(arm(data,length,boundary,gear,anchors,anchor_count,1,&cc,&cs,&cp,&cl))return -4;c1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)if(arm(data,length,boundary,gear,anchors,anchor_count,1,&cc,&cs,&cp,&cl))return -5;c2=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)if(arm(data,length,boundary,gear,anchors,anchor_count,0,&bc,&bs,&bp,&bl))return -6;b2=now_ns()-t;
    out->baseline_ns_per_call=((double)b1+(double)b2)/(2.0*(double)batch);
    out->candidate_ns_per_call=((double)c1+(double)c2)/(2.0*(double)batch);
    out->baseline_dispatch_path=bp;out->candidate_dispatch_path=cp;
    out->baseline_final_law=bl;out->candidate_final_law=cl;
    out->baseline_consumer=bc;out->candidate_consumer=cc;out->baseline_safe=bs;out->candidate_safe=cs;
    return 0;
}
