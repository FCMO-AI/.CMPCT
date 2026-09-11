#define _POSIX_C_SOURCE 200809L
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_FROZEN_LEAF 192u
#define LEAF_PREFIX_BYTES 22u
#define LEAF_SCRATCH_BYTES (LEAF_PREFIX_BYTES + MAX_FROZEN_LEAF)
#define PARENT_SCRATCH_BYTES 74u
#define ROOT_SCRATCH_BYTES 50u

static void le32(unsigned char *p,uint32_t x){for(int i=0;i<4;i++)p[i]=(unsigned char)(x>>(8*i));}
static void le64(unsigned char *p,uint64_t x){for(int i=0;i<8;i++)p[i]=(unsigned char)(x>>(8*i));}
static uint64_t ns(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC_RAW,&t)!=0)abort();return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
static int cmp_u64(const void *a,const void *b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return x<y?-1:x>y?1:0;}

static void leaf_hash_baseline(uint64_t idx,uint64_t total,const unsigned char *p,size_t n,unsigned char out[32]){
    SHA256_CTX c; unsigned char meta[16]; le64(meta,idx); le64(meta+8,total);
    SHA256_Init(&c); SHA256_Update(&c,"ONE-L\0",6); SHA256_Update(&c,meta,16); SHA256_Update(&c,p,n); SHA256_Final(out,&c);
}
static void parent_hash_baseline(uint32_t level,const unsigned char left[32],const unsigned char right[32],unsigned char out[32]){
    SHA256_CTX c; unsigned char lev[4]; le32(lev,level);
    SHA256_Init(&c); SHA256_Update(&c,"ONE-P\0",6); SHA256_Update(&c,lev,4); SHA256_Update(&c,left,32); SHA256_Update(&c,right,32); SHA256_Final(out,&c);
}
static void root_hash_baseline(uint64_t total,uint32_t leaf,const unsigned char tree[32],unsigned char out[32]){
    SHA256_CTX c; unsigned char meta[12]; le64(meta,total); le32(meta+8,leaf);
    SHA256_Init(&c); SHA256_Update(&c,"ONE-R\0",6); SHA256_Update(&c,meta,12); SHA256_Update(&c,tree,32); SHA256_Final(out,&c);
}

static int leaf_hash_candidate(uint64_t idx,uint64_t total,const unsigned char *p,size_t n,unsigned char out[32]){
    unsigned char msg[LEAF_SCRATCH_BYTES];
    if(n>MAX_FROZEN_LEAF)return 0;
    memcpy(msg,"ONE-L\0",6); le64(msg+6,idx); le64(msg+14,total); if(n)memcpy(msg+22,p,n);
    return SHA256(msg,22+n,out)!=NULL;
}
static int parent_hash_candidate(uint32_t level,const unsigned char left[32],const unsigned char right[32],unsigned char out[32]){
    unsigned char msg[PARENT_SCRATCH_BYTES];
    memcpy(msg,"ONE-P\0",6); le32(msg+6,level); memcpy(msg+10,left,32); memcpy(msg+42,right,32);
    return SHA256(msg,sizeof(msg),out)!=NULL;
}
static int root_hash_candidate(uint64_t total,uint32_t leaf,const unsigned char tree[32],unsigned char out[32]){
    unsigned char msg[ROOT_SCRATCH_BYTES];
    memcpy(msg,"ONE-R\0",6); le64(msg+6,total); le32(msg+14,leaf); memcpy(msg+18,tree,32);
    return SHA256(msg,sizeof(msg),out)!=NULL;
}

static size_t geometry_node_count(size_t total,uint32_t leaf){
    size_t width=(total+leaf-1)/leaf; if(width==0)width=1; size_t nodes=width;
    while(width>1){width=(width+1)/2; nodes+=width;}
    return nodes+1; /* explicit root commitment */
}

static int build_baseline(const unsigned char *data,size_t total,uint32_t leaf,unsigned char root[32]){
    size_t count=(total+leaf-1)/leaf; if(count==0)count=1;
    unsigned char *cur=malloc(count*32), *next=malloc(((count+1)/2)*32);
    if(!cur||!next){free(cur);free(next);return 0;}
    for(size_t i=0;i<count;i++){
        size_t off=i*(size_t)leaf, len=off<total?total-off:0; if(len>leaf)len=leaf;
        leaf_hash_baseline(i,total,data+off,len,cur+i*32);
    }
    uint32_t level=1; size_t width=count;
    while(width>1){
        size_t nw=(width+1)/2;
        for(size_t i=0;i<nw;i++){
            const unsigned char *l=cur+(2*i)*32; const unsigned char *r=(2*i+1<width)?cur+(2*i+1)*32:l;
            parent_hash_baseline(level,l,r,next+i*32);
        }
        unsigned char *tmp=cur;cur=next;next=tmp;width=nw;level++;
    }
    root_hash_baseline(total,leaf,cur,root); free(cur);free(next);return 1;
}

static int build_candidate(const unsigned char *data,size_t total,uint32_t leaf,unsigned char root[32]){
    if(leaf>MAX_FROZEN_LEAF)return 0;
    size_t count=(total+leaf-1)/leaf; if(count==0)count=1;
    unsigned char *cur=malloc(count*32), *next=malloc(((count+1)/2)*32);
    if(!cur||!next){free(cur);free(next);return 0;}
    for(size_t i=0;i<count;i++){
        size_t off=i*(size_t)leaf, len=off<total?total-off:0; if(len>leaf)len=leaf;
        if(!leaf_hash_candidate(i,total,data+off,len,cur+i*32)){free(cur);free(next);return 0;}
    }
    uint32_t level=1; size_t width=count;
    while(width>1){
        size_t nw=(width+1)/2;
        for(size_t i=0;i<nw;i++){
            const unsigned char *l=cur+(2*i)*32; const unsigned char *r=(2*i+1<width)?cur+(2*i+1)*32:l;
            if(!parent_hash_candidate(level,l,r,next+i*32)){free(cur);free(next);return 0;}
        }
        unsigned char *tmp=cur;cur=next;next=tmp;width=nw;level++;
    }
    if(!root_hash_candidate(total,leaf,cur,root)){free(cur);free(next);return 0;}
    free(cur);free(next);return 1;
}

static void print_hex(const unsigned char x[32]){for(int i=0;i<32;i++)printf("%02x",x[i]);}

int main(int argc,char **argv){
    if(argc!=4){fprintf(stderr,"usage: %s bytes leaf reps\n",argv[0]);return 2;}
    size_t total=(size_t)strtoull(argv[1],NULL,10); uint32_t leaf=(uint32_t)strtoul(argv[2],NULL,10); int reps=atoi(argv[3]);
    if(!total||!leaf||leaf>MAX_FROZEN_LEAF||reps<3)return 2;
    unsigned char *data=malloc(total); uint64_t *base=malloc(sizeof(uint64_t)*(size_t)reps),*cand=malloc(sizeof(uint64_t)*(size_t)reps);
    if(!data||!base||!cand){free(data);free(base);free(cand);return 3;}
    for(size_t i=0;i<total;i++)data[i]=(unsigned char)(((i*131u)^(i>>3)^(i>>11)^0x5au)&255u);
    unsigned char br[32],cr[32];
    if(!build_baseline(data,total,leaf,br)||!build_candidate(data,total,leaf,cr)||memcmp(br,cr,32)!=0){free(data);free(base);free(cand);return 4;}
    for(int w=0;w<3;w++){if(!build_baseline(data,total,leaf,br)||!build_candidate(data,total,leaf,cr)){free(data);free(base);free(cand);return 4;}}
    for(int r=0;r<reps;r++){
        uint64_t t;
        if((r&1)==0){
            t=ns(); if(!build_baseline(data,total,leaf,br))return 4; base[r]=ns()-t;
            t=ns(); if(!build_candidate(data,total,leaf,cr))return 4; cand[r]=ns()-t;
        }else{
            t=ns(); if(!build_candidate(data,total,leaf,cr))return 4; cand[r]=ns()-t;
            t=ns(); if(!build_baseline(data,total,leaf,br))return 4; base[r]=ns()-t;
        }
    }
    if(memcmp(br,cr,32)!=0){free(data);free(base);free(cand);return 4;}
    qsort(base,(size_t)reps,sizeof(uint64_t),cmp_u64); qsort(cand,(size_t)reps,sizeof(uint64_t),cmp_u64);
    printf("{\"root_bytes\":%zu,\"leaf_bytes\":%u,\"reps\":%d,\"node_count\":%zu,\"scratch_bytes\":%u,\"baseline_median_ns\":%llu,\"candidate_median_ns\":%llu,\"candidate_ratio\":%.9f,\"baseline_root\":\"",total,leaf,reps,geometry_node_count(total,leaf),(unsigned)LEAF_SCRATCH_BYTES,(unsigned long long)base[reps/2],(unsigned long long)cand[reps/2],(double)cand[reps/2]/(double)base[reps/2]);
    print_hex(br); printf("\",\"candidate_root\":\""); print_hex(cr); printf("\"}\n");
    free(data);free(base);free(cand);return 0;
}
