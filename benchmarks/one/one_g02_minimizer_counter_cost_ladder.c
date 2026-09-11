#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct {
    uint64_t final_state;
    uint64_t positions_considered;
    uint64_t reserved_state_bytes;
    uint64_t derived_state_reads;
    uint64_t suffix_blocks_built;
    uint64_t suffix_blocks_skipped_dead;
    uint64_t checksum;
} one_g02_counter_cost_result;

static inline void barrier(void *p) {
#if defined(__GNUC__) || defined(__clang__)
    __asm__ __volatile__("" : : "r"(p) : "memory");
#else
    (void)p;
#endif
}

int one_g02_counter_buffer_prefix_cost_kernel(const uint8_t *data,size_t length,const uint64_t gear[256],size_t window,size_t minimizer_span,one_g02_counter_cost_result *out) {
    if(!out||!gear||!window||!minimizer_span||minimizer_span%4) return -1;
    const size_t bs=minimizer_span/4; *out=(one_g02_counter_cost_result){0}; if(!length) return 0; if(!data) return -1;
    const int enabled=length>=minimizer_span+window; uint64_t *values=NULL;
    if(enabled){ values=malloc(bs*sizeof(uint64_t)); if(!values)return -2; out->reserved_state_bytes=bs*sizeof(uint64_t)+4*3*sizeof(uint64_t); }
    uint64_t bmin[4]={0},bpos[4]={0},bnum[4]={UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX};
    uint64_t state=0,pmin=0,ppos=0,q=0; size_t r=0;
    for(size_t pos=0;pos<length;++pos){ state=(state<<1)+gear[data[pos]]; if(pos+1<window)continue; out->positions_considered++; if(!enabled)continue;
        if(r==0){pmin=state;ppos=pos;} else if(state<=pmin){pmin=state;ppos=pos;} values[r]=state;
        if(r+1==bs){size_t slot=(size_t)(q&3u);bmin[slot]=pmin;bpos[slot]=ppos;bnum[slot]=q;out->checksum^=bmin[slot]+bpos[slot]+bnum[slot];barrier(values);r=0;q++;}else r++;
    }
    out->final_state=state; free(values); return 0;
}

int one_g02_counter_dense_suffix_cost_kernel(const uint8_t *data,size_t length,const uint64_t gear[256],size_t window,size_t minimizer_span,one_g02_counter_cost_result *out) {
    if(!out||!gear||!window||!minimizer_span||minimizer_span%4) return -1; const size_t bs=minimizer_span/4; if(bs>UINT16_MAX)return -1;
    *out=(one_g02_counter_cost_result){0}; if(!length)return 0;if(!data)return -1; const int enabled=length>=minimizer_span+window; const uint64_t total=length>=window?(uint64_t)(length-window+1):0;
    uint64_t *values=NULL,*svals=NULL; uint16_t *soffs=NULL; if(enabled){values=malloc(bs*8);svals=malloc(4*bs*8);soffs=malloc(4*bs*2);if(!values||!svals||!soffs){free(values);free(svals);free(soffs);return -2;}out->reserved_state_bytes=bs*8+4*bs*(8+2)+4*3*8;}
    uint64_t bmin[4]={0},bpos[4]={0},bnum[4]={UINT64_MAX,UINT64_MAX,UINT64_MAX,UINT64_MAX}; uint64_t state=0,pmin=0,ppos=0,q=0;size_t r=0;
    for(size_t pos=0;pos<length;++pos){state=(state<<1)+gear[data[pos]];if(pos+1<window)continue;out->positions_considered++;if(!enabled)continue;
        if(r==0){pmin=state;ppos=pos;}else if(state<=pmin){pmin=state;ppos=pos;}values[r]=state;
        if(r+1==bs){size_t slot=(size_t)(q&3u);uint64_t first=(q+4)*(uint64_t)bs;if(total>first){size_t base=slot*bs,i=bs-1;svals[base+i]=values[i];soffs[base+i]=(uint16_t)i;out->derived_state_reads++;while(i>0){size_t c=i-1;uint64_t v=values[c];if(v<svals[base+i]){svals[base+c]=v;soffs[base+c]=(uint16_t)c;}else{svals[base+c]=svals[base+i];soffs[base+c]=soffs[base+i];}out->derived_state_reads++;i=c;}barrier(svals+base);barrier(soffs+base);out->checksum^=svals[base]+soffs[base];out->suffix_blocks_built++;}else out->suffix_blocks_skipped_dead++;bmin[slot]=pmin;bpos[slot]=ppos;bnum[slot]=q;out->checksum^=bmin[slot]+bpos[slot]+bnum[slot];r=0;q++;}else r++;
    }
    out->final_state=state;free(values);free(svals);free(soffs);return 0;
}
