#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t samples, zero_shift_matches, coverage_compared_bytes, best_hits;
    int64_t best_shift;
    uint64_t proof_attempts, exact_proofs, proof_compared_bytes, strata_with_support;
} one_g02_dispatch_result;

typedef struct {
    double dispatch_ns_per_call, direct_ns_per_call, half_ns_per_call;
    int dispatch_path;
    one_g02_dispatch_result dispatch_result, direct_result, half_result;
} one_g02_dispatch_measurement;

extern int one_g02_shift_relation_safe_dispatch(const uint8_t *,const uint8_t *,size_t,one_g02_dispatch_result *);
extern int one_g02_shift_branch_bound_relation_direct(const uint8_t *,const uint8_t *,size_t,one_g02_dispatch_result *);
extern int one_g02_shift_branch_bound_proof_led(const uint8_t *,size_t,one_g02_dispatch_result *);
static uint64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;}

int one_g02_shift_relation_safe_dispatch_measure(const uint8_t *packed,size_t relation_len,size_t batch,one_g02_dispatch_measurement *out){
    if(!packed||!out||relation_len<1024||!batch)return -1;
    const uint8_t *src=packed,*dst=packed+relation_len; size_t n=relation_len*2;
    one_g02_dispatch_result sr={0},dr={0},hr={0}; int path=one_g02_shift_relation_safe_dispatch(src,dst,relation_len,&sr);
    if(path<0||one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,&dr)||one_g02_shift_branch_bound_proof_led(packed,n,&hr))return -2;
    uint64_t t,d1,d2,s1,s2,s3,s4,h1,h2;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,&dr);d1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_relation_safe_dispatch(src,dst,relation_len,&sr);s1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_relation_safe_dispatch(src,dst,relation_len,&sr);s2=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_branch_bound_relation_direct(src,dst,relation_len,&dr);d2=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_branch_bound_proof_led(packed,n,&hr);h1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_relation_safe_dispatch(src,dst,relation_len,&sr);s3=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_relation_safe_dispatch(src,dst,relation_len,&sr);s4=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;++i)one_g02_shift_branch_bound_proof_led(packed,n,&hr);h2=now_ns()-t;
    out->direct_ns_per_call=((double)d1+d2)/(2.0*batch); out->dispatch_ns_per_call=((double)s1+s2+s3+s4)/(4.0*batch); out->half_ns_per_call=((double)h1+h2)/(2.0*batch);
    out->dispatch_path=path;out->dispatch_result=sr;out->direct_result=dr;out->half_result=hr;return 0;
}
