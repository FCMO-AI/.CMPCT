#define _POSIX_C_SOURCE 200809L
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static void le32(unsigned char *p,uint32_t x){for(int i=0;i<4;i++)p[i]=(unsigned char)(x>>(8*i));}
static void le64(unsigned char *p,uint64_t x){for(int i=0;i<8;i++)p[i]=(unsigned char)(x>>(8*i));}
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}

static void leaf_hash(uint64_t idx,uint64_t total,const unsigned char *p,size_t n,unsigned char out[32]){
    SHA256_CTX c; unsigned char meta[16]; le64(meta,idx); le64(meta+8,total);
    SHA256_Init(&c); SHA256_Update(&c,"ONE-L\0",6); SHA256_Update(&c,meta,16); SHA256_Update(&c,p,n); SHA256_Final(out,&c);
}
static void parent_hash(uint32_t level,const unsigned char left[32],const unsigned char right[32],unsigned char out[32]){
    SHA256_CTX c; unsigned char lev[4]; le32(lev,level);
    SHA256_Init(&c); SHA256_Update(&c,"ONE-P\0",6); SHA256_Update(&c,lev,4); SHA256_Update(&c,left,32); SHA256_Update(&c,right,32); SHA256_Final(out,&c);
}
static void root_commit(uint64_t total,uint32_t leaf,const unsigned char tree[32],unsigned char out[32]){
    SHA256_CTX c; unsigned char meta[12]; le64(meta,total); le32(meta+8,leaf);
    SHA256_Init(&c); SHA256_Update(&c,"ONE-R\0",6); SHA256_Update(&c,meta,12); SHA256_Update(&c,tree,32); SHA256_Final(out,&c);
}

static int build(const unsigned char *data,size_t total,uint32_t leaf,unsigned char root[32]){
    size_t count=(total+leaf-1)/leaf; if(count==0)count=1;
    unsigned char *cur=malloc(count*32), *next=malloc(((count+1)/2)*32);
    if(!cur||!next){free(cur);free(next);return 0;}
    for(size_t i=0;i<count;i++){
        size_t off=i*(size_t)leaf, len=off<total?total-off:0; if(len>leaf)len=leaf;
        leaf_hash(i,total,data+off,len,cur+i*32);
    }
    uint32_t level=1; size_t width=count;
    while(width>1){
        size_t nw=(width+1)/2;
        for(size_t i=0;i<nw;i++){
            unsigned char *l=cur+(2*i)*32; unsigned char *r=(2*i+1<width)?cur+(2*i+1)*32:l;
            parent_hash(level,l,r,next+i*32);
        }
        unsigned char *tmp=cur;cur=next;next=tmp;width=nw;level++;
    }
    root_commit(total,leaf,cur,root); free(cur);free(next);return 1;
}

static int cmp_u64(const void *a,const void *b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return x<y?-1:x>y;}
int main(int argc,char **argv){
    if(argc!=4){fprintf(stderr,"usage: %s bytes leaf reps\n",argv[0]);return 2;}
    size_t total=(size_t)strtoull(argv[1],0,10); uint32_t leaf=(uint32_t)strtoul(argv[2],0,10); int reps=atoi(argv[3]);
    if(!total||!leaf||reps<3)return 2;
    unsigned char *data=malloc(total); uint64_t *tree=malloc(sizeof(uint64_t)*reps),*whole=malloc(sizeof(uint64_t)*reps); if(!data||!tree||!whole)return 3;
    for(size_t i=0;i<total;i++) data[i]=(unsigned char)(((i*131u) ^ (i>>3) ^ (i>>11) ^ 0x5au)&255u);
    unsigned char root[32],digest[32]; build(data,total,leaf,root); SHA256(data,total,digest);
    for(int r=0;r<reps;r++){
        uint64_t t=ns(); build(data,total,leaf,root); tree[r]=ns()-t;
        t=ns(); SHA256(data,total,digest); whole[r]=ns()-t;
    }
    qsort(tree,reps,sizeof(uint64_t),cmp_u64); qsort(whole,reps,sizeof(uint64_t),cmp_u64);
    printf("{\"root_bytes\":%zu,\"leaf_bytes\":%u,\"reps\":%d,\"tree_median_ns\":%llu,\"whole_median_ns\":%llu,\"elapsed_ratio\":%.9f,\"tree_root\":\"",total,leaf,reps,(unsigned long long)tree[reps/2],(unsigned long long)whole[reps/2],(double)tree[reps/2]/(double)whole[reps/2]);
    for(int i=0;i<32;i++)printf("%02x",root[i]); printf("\"}\n");
    free(data);free(tree);free(whole);return 0;
}
