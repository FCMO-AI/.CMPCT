#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * ONE-G0.2 native causal-transfer consumer for relation witness deferral.
 * It consumes an already-proven native minimizer trace. Both modes share the
 * same demand-grown indexing/verification path and stop relation-specific
 * auditions after the first cross-object nomination. witness_only=0 performs
 * inherited left/right extension before nomination; witness_only=1 lets an
 * exact 64-B cross witness nominate the pair for the external safe proof.
 * The witness is never Law authority. Research-only, not product ABI.
 */
#define ONE_G02_WINDOW 64u
#define ONE_G02_PROOF_BLOCK 4096u
#define ONE_G02_LOCAL_ENTRIES 64u
#define ONE_G02_GLOBAL_ENTRIES 8192u
#define ONE_G02_GLOBAL_INITIAL_ENTRIES 64u

typedef struct {
    uint64_t cross_auditions;
    uint64_t cross_witnesses;
    uint64_t nominations;
    uint64_t local_peak_entries;
    uint64_t global_peak_entries;
    uint64_t global_capacity_entries;
    uint64_t verification_read_bytes;
    uint64_t extension_read_bytes;
    uint64_t anchors_consumed;
} one_g02_witness_consumer_result;

typedef struct { uint64_t key; size_t start; int used; } one_g02_index_entry;

static size_t min_size(size_t a,size_t b){return a<b?a:b;}
static int find_entry(const one_g02_index_entry *e,size_t cap,size_t count,size_t head,uint64_t key,size_t *out){
    if(!e||!cap||count>cap)return 0;
    for(size_t i=0;i<count;++i){size_t s=(head+i)%cap;if(e[s].used&&e[s].key==key){*out=e[s].start;return 1;}}
    return 0;
}
static size_t extend_left(const uint8_t *data,size_t source,size_t target,size_t covered,uint64_t *reads){
    size_t max=min_size(source,target-covered),matched=0;
    while(matched<max){size_t step=min_size(ONE_G02_PROOF_BLOCK,max-matched);size_t ss=source-matched-step,ts=target-matched-step;
        *reads+=2u*(uint64_t)step;
        if(memcmp(data+ss,data+ts,step)==0){matched+=step;continue;}
        for(size_t off=1;off<=step;++off){*reads+=2;if(data[source-matched-off]!=data[target-matched-off])return matched+off-1;}matched+=step;
    }return matched;
}
static size_t extend_right(const uint8_t *data,size_t length,size_t source,size_t target,uint64_t *reads){
    size_t max=min_size(target-source,length-target),matched=ONE_G02_WINDOW;
    while(matched<max){size_t step=min_size(ONE_G02_PROOF_BLOCK,max-matched);*reads+=2u*(uint64_t)step;
        if(memcmp(data+source+matched,data+target+matched,step)==0){matched+=step;continue;}
        for(size_t off=0;off<step;++off){*reads+=2;if(data[source+matched+off]!=data[target+matched+off])return matched+off;}matched+=step;
    }return matched;
}
static void audition(const uint8_t *data,size_t length,size_t boundary,size_t start,int have,size_t prior,int witness_only,size_t *covered,int *nominated,one_g02_witness_consumer_result *out){
    if(*nominated||!have||start<*covered)return;
    int cross=prior<boundary&&boundary<=start;
    if(cross)out->cross_auditions++;
    out->verification_read_bytes+=2u*ONE_G02_WINDOW;
    if(memcmp(data+prior,data+start,ONE_G02_WINDOW)!=0)return;
    if(cross){out->cross_witnesses++;if(witness_only){*nominated=1;out->nominations=1;return;}}
    uint64_t reads=0;size_t left=extend_left(data,prior,start,*covered,&reads);size_t right=extend_right(data,length,prior,start,&reads);out->extension_read_bytes+=reads;
    size_t ls=start-left,ts=ls>*covered?ls:*covered,te=start+right;if(te<=ts)return;
    if(cross){*nominated=1;out->nominations=1;}
    *covered=te;
}

int one_g02_native_witness_deferral_consume(const uint8_t *data,size_t length,size_t boundary,const uint64_t gear[256],const uint64_t *anchors,size_t anchor_count,int witness_only,one_g02_witness_consumer_result *out){
    if(!out||!gear||(witness_only!=0&&witness_only!=1))return -1;*out=(one_g02_witness_consumer_result){0};
    if(length==0)return anchor_count==0?0:-3;if(!data||boundary>length||(anchor_count&&!anchors))return -1;
    one_g02_index_entry local[ONE_G02_LOCAL_ENTRIES]={{0}};one_g02_index_entry *global=NULL;
    size_t global_capacity=0,local_head=0,local_count=0,global_count=0,anchor_i=0,covered=0;int nominated=0;uint64_t h=0;uint8_t run_value=data[0];size_t run_length=0;int rc=0;
    for(size_t position=0;position<length;++position){uint8_t value=data[position];
        if(!run_length){run_value=value;run_length=1;}else if(value==run_value)run_length++;else{run_value=value;run_length=1;}
        h=(h<<1)+gear[value];if(position+1<ONE_G02_WINDOW)continue;size_t start=position+1-ONE_G02_WINDOW;int run_dominated=run_length>=ONE_G02_WINDOW;
        if(!run_dominated&&((position+1)%ONE_G02_WINDOW)==0){size_t prior=0;int have=find_entry(local,ONE_G02_LOCAL_ENTRIES,local_count,local_head,h,&prior);
            audition(data,length,boundary,start,have,prior,witness_only,&covered,&nominated,out);
            if(!have){size_t slot;if(local_count<ONE_G02_LOCAL_ENTRIES){slot=(local_head+local_count)%ONE_G02_LOCAL_ENTRIES;local_count++;}else{slot=local_head;local_head=(local_head+1)%ONE_G02_LOCAL_ENTRIES;}
                local[slot].key=h;local[slot].start=start;local[slot].used=1;if(local_count>out->local_peak_entries)out->local_peak_entries=local_count;}}
        if(anchor_i<anchor_count){uint64_t anchor=anchors[anchor_i];if(anchor<position){rc=-4;goto done;}if(anchor==position){size_t prior=0;int have=find_entry(global,global_capacity,global_count,0,h,&prior);
                audition(data,length,boundary,start,have,prior,witness_only,&covered,&nominated,out);
                if(!have&&global_count<ONE_G02_GLOBAL_ENTRIES){
                    if(global_count==global_capacity){size_t nc=global_capacity?global_capacity*2:ONE_G02_GLOBAL_INITIAL_ENTRIES;if(nc>ONE_G02_GLOBAL_ENTRIES)nc=ONE_G02_GLOBAL_ENTRIES;
                        one_g02_index_entry *grown=(one_g02_index_entry*)realloc(global,nc*sizeof(*global));if(!grown){rc=-6;goto done;}global=grown;global_capacity=nc;}
                    global[global_count].key=h;global[global_count].start=start;global[global_count].used=1;global_count++;if(global_count>out->global_peak_entries)out->global_peak_entries=global_count;}
                anchor_i++;out->anchors_consumed++;}}
    }
    if(anchor_i!=anchor_count)rc=-5;
done:
    out->global_capacity_entries=global_capacity;free(global);return rc;
}
