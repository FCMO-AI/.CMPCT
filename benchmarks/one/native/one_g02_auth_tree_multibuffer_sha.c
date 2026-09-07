#define _POSIX_C_SOURCE 200809L
#include <intel-ipsec-mb.h>
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_FROZEN_LEAF 192u
#define MAX_MESSAGE_BYTES (22u + MAX_FROZEN_LEAF)

static void le32(unsigned char *p,uint32_t x){for(int i=0;i<4;i++)p[i]=(unsigned char)(x>>(8*i));}
static void le64(unsigned char *p,uint64_t x){for(int i=0;i<8;i++)p[i]=(unsigned char)(x>>(8*i));}
static uint64_t clock_ns(clockid_t id){struct timespec t;if(clock_gettime(id,&t)!=0)abort();return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
static uint64_t wall_ns(void){return clock_ns(CLOCK_MONOTONIC_RAW);}
static uint64_t cpu_ns(void){return clock_ns(CLOCK_PROCESS_CPUTIME_ID);}
static int cmp_u64(const void *a,const void *b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return x<y?-1:x>y?1:0;}

static void leaf_hash_baseline(uint64_t idx,uint64_t total,const unsigned char *p,size_t n,unsigned char out[32]){
    SHA256_CTX c;unsigned char meta[16];le64(meta,idx);le64(meta+8,total);
    SHA256_Init(&c);SHA256_Update(&c,"ONE-L\0",6);SHA256_Update(&c,meta,16);SHA256_Update(&c,p,n);SHA256_Final(out,&c);
}
static void parent_hash_baseline(uint32_t level,const unsigned char left[32],const unsigned char right[32],unsigned char out[32]){
    SHA256_CTX c;unsigned char lev[4];le32(lev,level);
    SHA256_Init(&c);SHA256_Update(&c,"ONE-P\0",6);SHA256_Update(&c,lev,4);SHA256_Update(&c,left,32);SHA256_Update(&c,right,32);SHA256_Final(out,&c);
}
static void root_hash_baseline(uint64_t total,uint32_t leaf,const unsigned char tree[32],unsigned char out[32]){
    SHA256_CTX c;unsigned char meta[12];le64(meta,total);le32(meta+8,leaf);
    SHA256_Init(&c);SHA256_Update(&c,"ONE-R\0",6);SHA256_Update(&c,meta,12);SHA256_Update(&c,tree,32);SHA256_Final(out,&c);
}

static size_t geometry(size_t total,uint32_t leaf,size_t *leaves,size_t *parents,size_t *levels){
    size_t width=(total+leaf-1)/leaf;if(width==0)width=1;
    *leaves=width;*parents=0;*levels=0;
    while(width>1){width=(width+1)/2;*parents+=width;(*levels)++;}
    return *leaves+*parents+1;
}

static size_t tree_workspace_bytes(size_t total,uint32_t leaf){
    size_t count=(total+leaf-1)/leaf;if(count==0)count=1;
    return count*32u+((count+1u)/2u)*32u;
}

static size_t multibuffer_extra_workspace_bytes(void){
    return (size_t)IMB_MAX_BURST_SIZE*(sizeof(IMB_JOB)+MAX_MESSAGE_BYTES+sizeof(size_t));
}

static int build_baseline(const unsigned char *data,size_t total,uint32_t leaf,unsigned char root[32]){
    size_t count=(total+leaf-1)/leaf;if(count==0)count=1;
    unsigned char *cur=malloc(count*32),*next=malloc(((count+1)/2)*32);
    if(!cur||!next){free(cur);free(next);return 0;}
    for(size_t i=0;i<count;i++){
        size_t off=i*(size_t)leaf,len=off<total?total-off:0;if(len>leaf)len=leaf;
        leaf_hash_baseline(i,total,data+off,len,cur+i*32);
    }
    uint32_t level=1;size_t width=count;
    while(width>1){
        size_t nw=(width+1)/2;
        for(size_t i=0;i<nw;i++){
            const unsigned char *l=cur+(2*i)*32,*r=(2*i+1<width)?cur+(2*i+1)*32:l;
            parent_hash_baseline(level,l,r,next+i*32);
        }
        unsigned char *tmp=cur;cur=next;next=tmp;width=nw;level++;
    }
    root_hash_baseline(total,leaf,cur,root);free(cur);free(next);return 1;
}

static int submit_sha256(IMB_MGR *mgr,IMB_JOB *jobs,unsigned char *arena,const size_t *lengths,size_t n,unsigned char *out){
    for(size_t i=0;i<n;i++){
        IMB_JOB *job=&jobs[i];memset(job,0,sizeof(*job));
        job->enc_keys=NULL;job->dec_keys=NULL;
        job->cipher_direction=IMB_DIR_ENCRYPT;
        job->chain_order=IMB_ORDER_HASH_CIPHER;
        job->auth_tag_output=out+i*32;
        job->auth_tag_output_len_in_bytes=32;
        job->src=arena+i*MAX_MESSAGE_BYTES;
        job->msg_len_to_hash_in_bytes=lengths[i];
        job->cipher_mode=IMB_CIPHER_NULL;
        job->hash_alg=IMB_AUTH_SHA_256;
    }
    const uint32_t done=IMB_SUBMIT_HASH_BURST(mgr,jobs,(uint32_t)n,IMB_AUTH_SHA_256);
    if(done!=(uint32_t)n)return 0;
    for(size_t i=0;i<n;i++)if(jobs[i].status!=IMB_STATUS_COMPLETED)return 0;
    return 1;
}

static int build_candidate(IMB_MGR *mgr,const unsigned char *data,size_t total,uint32_t leaf,unsigned char root[32],uint64_t *staged_bytes){
    if(leaf>MAX_FROZEN_LEAF)return 0;
    size_t count=(total+leaf-1)/leaf;if(count==0)count=1;
    unsigned char *cur=malloc(count*32),*next=malloc(((count+1)/2)*32);
    IMB_JOB *jobs=calloc(IMB_MAX_BURST_SIZE,sizeof(*jobs));
    unsigned char *arena=malloc((size_t)IMB_MAX_BURST_SIZE*MAX_MESSAGE_BYTES);
    size_t *lengths=malloc((size_t)IMB_MAX_BURST_SIZE*sizeof(*lengths));
    if(!cur||!next||!jobs||!arena||!lengths){free(cur);free(next);free(jobs);free(arena);free(lengths);return 0;}
    *staged_bytes=0;

    for(size_t base=0;base<count;base+=IMB_MAX_BURST_SIZE){
        size_t batch=count-base;if(batch>IMB_MAX_BURST_SIZE)batch=IMB_MAX_BURST_SIZE;
        for(size_t j=0;j<batch;j++){
            size_t i=base+j,off=i*(size_t)leaf,len=off<total?total-off:0;if(len>leaf)len=leaf;
            unsigned char *m=arena+j*MAX_MESSAGE_BYTES;
            memcpy(m,"ONE-L\0",6);le64(m+6,i);le64(m+14,total);if(len)memcpy(m+22,data+off,len);
            lengths[j]=22+len;*staged_bytes+=(uint64_t)lengths[j];
        }
        if(!submit_sha256(mgr,jobs,arena,lengths,batch,cur+base*32))goto fail;
    }

    uint32_t level=1;size_t width=count;
    while(width>1){
        size_t nw=(width+1)/2;
        for(size_t base=0;base<nw;base+=IMB_MAX_BURST_SIZE){
            size_t batch=nw-base;if(batch>IMB_MAX_BURST_SIZE)batch=IMB_MAX_BURST_SIZE;
            for(size_t j=0;j<batch;j++){
                size_t i=base+j;const unsigned char *l=cur+(2*i)*32,*r=(2*i+1<width)?cur+(2*i+1)*32:l;
                unsigned char *m=arena+j*MAX_MESSAGE_BYTES;
                memcpy(m,"ONE-P\0",6);le32(m+6,level);memcpy(m+10,l,32);memcpy(m+42,r,32);
                lengths[j]=74;*staged_bytes+=74;
            }
            if(!submit_sha256(mgr,jobs,arena,lengths,batch,next+base*32))goto fail;
        }
        unsigned char *tmp=cur;cur=next;next=tmp;width=nw;level++;
    }

    memcpy(arena,"ONE-R\0",6);le64(arena+6,total);le32(arena+14,leaf);memcpy(arena+18,cur,32);lengths[0]=50;*staged_bytes+=50;
    if(!submit_sha256(mgr,jobs,arena,lengths,1,root))goto fail;
    free(cur);free(next);free(jobs);free(arena);free(lengths);return 1;
fail:
    free(cur);free(next);free(jobs);free(arena);free(lengths);return 0;
}

static void print_hex(const unsigned char x[32]){for(int i=0;i<32;i++)printf("%02x",x[i]);}

int main(int argc,char **argv){
    if(argc!=4){fprintf(stderr,"usage: %s bytes leaf reps\n",argv[0]);return 2;}
    size_t total=(size_t)strtoull(argv[1],NULL,10);uint32_t leaf=(uint32_t)strtoul(argv[2],NULL,10);int reps=atoi(argv[3]);
    if(!total||!leaf||leaf>MAX_FROZEN_LEAF||reps<3)return 2;
    unsigned char *data=malloc(total);
    uint64_t *base=malloc(sizeof(uint64_t)*(size_t)reps),*cand=malloc(sizeof(uint64_t)*(size_t)reps);
    uint64_t *base_cpu=malloc(sizeof(uint64_t)*(size_t)reps),*cand_cpu=malloc(sizeof(uint64_t)*(size_t)reps);
    if(!data||!base||!cand||!base_cpu||!cand_cpu){free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 3;}
    for(size_t i=0;i<total;i++)data[i]=(unsigned char)(((i*131u)^(i>>3)^(i>>11)^0x5au)&255u);

    IMB_MGR *mgr=alloc_mb_mgr(0);if(!mgr){free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 5;}
    IMB_ARCH arch;init_mb_mgr_auto(mgr,&arch);

    unsigned char br[32],cr[32];uint64_t staged=0,staged_check=0;
    if(!build_baseline(data,total,leaf,br)||!build_candidate(mgr,data,total,leaf,cr,&staged)||memcmp(br,cr,32)!=0){free_mb_mgr(mgr);free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 4;}
    for(int w=0;w<3;w++){
        if(!build_baseline(data,total,leaf,br)||!build_candidate(mgr,data,total,leaf,cr,&staged_check)){free_mb_mgr(mgr);free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 4;}
        if(staged_check!=staged){free_mb_mgr(mgr);free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 4;}
    }
    for(int r=0;r<reps;r++){
        uint64_t w0,w1,c0,c1;
        if((r&1)==0){
            c0=cpu_ns();w0=wall_ns();if(!build_baseline(data,total,leaf,br))return 4;w1=wall_ns();c1=cpu_ns();base[r]=w1-w0;base_cpu[r]=c1-c0;
            c0=cpu_ns();w0=wall_ns();if(!build_candidate(mgr,data,total,leaf,cr,&staged_check))return 4;w1=wall_ns();c1=cpu_ns();cand[r]=w1-w0;cand_cpu[r]=c1-c0;
        }else{
            c0=cpu_ns();w0=wall_ns();if(!build_candidate(mgr,data,total,leaf,cr,&staged_check))return 4;w1=wall_ns();c1=cpu_ns();cand[r]=w1-w0;cand_cpu[r]=c1-c0;
            c0=cpu_ns();w0=wall_ns();if(!build_baseline(data,total,leaf,br))return 4;w1=wall_ns();c1=cpu_ns();base[r]=w1-w0;base_cpu[r]=c1-c0;
        }
        if(staged_check!=staged)return 4;
    }
    if(memcmp(br,cr,32)!=0){free_mb_mgr(mgr);free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 4;}
    qsort(base,(size_t)reps,sizeof(uint64_t),cmp_u64);qsort(cand,(size_t)reps,sizeof(uint64_t),cmp_u64);
    qsort(base_cpu,(size_t)reps,sizeof(uint64_t),cmp_u64);qsort(cand_cpu,(size_t)reps,sizeof(uint64_t),cmp_u64);
    size_t leaves=0,parents=0,levels=0,nodes=geometry(total,leaf,&leaves,&parents,&levels);
    size_t baseline_workspace=tree_workspace_bytes(total,leaf),extra_workspace=multibuffer_extra_workspace_bytes();
    printf("{\"root_bytes\":%zu,\"leaf_bytes\":%u,\"reps\":%d,\"leaf_count\":%zu,\"parent_count\":%zu,\"level_count\":%zu,\"node_count\":%zu,\"burst_capacity\":%u,\"imb_arch\":%d,\"imb_features\":%llu,\"candidate_staged_bytes\":%llu,\"candidate_staged_over_source_ratio\":%.9f,\"baseline_explicit_workspace_bytes\":%zu,\"candidate_extra_explicit_workspace_bytes\":%zu,\"candidate_total_explicit_workspace_bytes\":%zu,\"baseline_median_ns\":%llu,\"candidate_median_ns\":%llu,\"candidate_ratio\":%.9f,\"baseline_cpu_median_ns\":%llu,\"candidate_cpu_median_ns\":%llu,\"candidate_cpu_ratio\":%.9f,\"baseline_root\":\"",total,leaf,reps,leaves,parents,levels,nodes,(unsigned)IMB_MAX_BURST_SIZE,(int)arch,(unsigned long long)mgr->features,(unsigned long long)staged,(double)staged/(double)total,baseline_workspace,extra_workspace,baseline_workspace+extra_workspace,(unsigned long long)base[reps/2],(unsigned long long)cand[reps/2],(double)cand[reps/2]/(double)base[reps/2],(unsigned long long)base_cpu[reps/2],(unsigned long long)cand_cpu[reps/2],(double)cand_cpu[reps/2]/(double)base_cpu[reps/2]);
    print_hex(br);printf("\",\"candidate_root\":\"");print_hex(cr);printf("\"}\n");
    free_mb_mgr(mgr);free(data);free(base);free(cand);free(base_cpu);free(cand_cpu);return 0;
}
