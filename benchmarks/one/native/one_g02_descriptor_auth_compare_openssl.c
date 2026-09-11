#define _POSIX_C_SOURCE 200809L
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_COUNT 8
#define MAX_LEVELS 5
#define HASH_BYTES 32
#define CONTROL_BYTES 40

typedef struct {
    uint32_t count;
    unsigned char control[MAX_COUNT][CONTROL_BYTES];
    uint32_t blob_len[MAX_COUNT];
    unsigned char *blob[MAX_COUNT];
} Input;

typedef struct {
    uint32_t widths[MAX_LEVELS];
    uint32_t nlevels;
    unsigned char h[MAX_LEVELS][MAX_COUNT][HASH_BYTES];
} Tree;

static volatile unsigned char sink_byte;

static uint64_t ns(void){
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*1000000000ull+(uint64_t)t.tv_nsec;
}
static void le32(unsigned char *p,uint32_t x){for(int i=0;i<4;i++)p[i]=(unsigned char)(x>>(8*i));}
static uint32_t rd32(FILE *f){
    unsigned char b[4]; if(fread(b,1,4,f)!=4){fprintf(stderr,"short input\n");exit(3);}
    return (uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);
}
static int cmp_u64(const void *a,const void *b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return x<y?-1:x>y;}

static void desc_leaf(uint32_t idx,const unsigned char control[CONTROL_BYTES],const unsigned char *blob,size_t blob_n,unsigned char out[32]){
    unsigned char sd[32],i4[4]; SHA256(blob,blob_n,sd); le32(i4,idx);
    SHA256_CTX c; SHA256_Init(&c);
    SHA256_Update(&c,"ONE-GDESC-L\0",sizeof("ONE-GDESC-L\0")-1);
    SHA256_Update(&c,i4,4); SHA256_Update(&c,control,CONTROL_BYTES); SHA256_Update(&c,sd,32); SHA256_Final(out,&c);
}
static void bparent(uint32_t level,const unsigned char left[32],const unsigned char right[32],unsigned char out[32]){
    unsigned char l4[4]; le32(l4,level); SHA256_CTX c; SHA256_Init(&c);
    SHA256_Update(&c,"ONE-GDESC-P\0",sizeof("ONE-GDESC-P\0")-1); SHA256_Update(&c,l4,4);
    SHA256_Update(&c,left,32); SHA256_Update(&c,right,32); SHA256_Final(out,&c);
}
static void qparent(uint32_t level,uint32_t count,const unsigned char children[MAX_COUNT][32],unsigned char out[32]){
    unsigned char meta[8]; le32(meta,level); le32(meta+4,count); SHA256_CTX c; SHA256_Init(&c);
    SHA256_Update(&c,"ONE-GDESC-QP\0",sizeof("ONE-GDESC-QP\0")-1); SHA256_Update(&c,meta,8);
    for(uint32_t i=0;i<count;i++)SHA256_Update(&c,children[i],32); SHA256_Final(out,&c);
}

static void build_binary(const Input *in,Tree *t){
    memset(t,0,sizeof(*t)); t->widths[0]=in->count; t->nlevels=1;
    for(uint32_t i=0;i<in->count;i++)desc_leaf(i,in->control[i],in->blob[i],in->blob_len[i],t->h[0][i]);
    uint32_t width=in->count,level=1;
    while(width>1){
        uint32_t nw=(width+1)/2; t->widths[level]=nw;
        for(uint32_t i=0;i<nw;i++){
            unsigned char *l=t->h[level-1][2*i];
            unsigned char *r=(2*i+1<width)?t->h[level-1][2*i+1]:l;
            bparent(level,l,r,t->h[level][i]);
        }
        width=nw; level++; t->nlevels=level;
    }
}
static void build_quaternary(const Input *in,Tree *t){
    memset(t,0,sizeof(*t)); t->widths[0]=in->count; t->nlevels=1;
    for(uint32_t i=0;i<in->count;i++)desc_leaf(i,in->control[i],in->blob[i],in->blob_len[i],t->h[0][i]);
    uint32_t width=in->count,level=1;
    while(width>1){
        uint32_t nw=(width+3)/4; t->widths[level]=nw;
        for(uint32_t p=0;p<nw;p++){
            uint32_t start=4*p,cc=width-start; if(cc>4)cc=4;
            unsigned char children[MAX_COUNT][32];
            for(uint32_t j=0;j<cc;j++)memcpy(children[j],t->h[level-1][start+j],32);
            qparent(level,cc,children,t->h[level][p]);
        }
        width=nw; level++; t->nlevels=level;
    }
}

static int verify_binary_index(const Input *in,const Tree *t,uint32_t index){
    unsigned char h[32]; desc_leaf(index,in->control[index],in->blob[index],in->blob_len[index],h);
    uint32_t cur=index,width=in->count;
    for(uint32_t level=0;width>1;level++){
        uint32_t sibling=cur^1u; const unsigned char *s=(sibling<width)?t->h[level][sibling]:h;
        unsigned char next[32];
        if((cur&1u)==0)bparent(level+1,h,s,next); else bparent(level+1,s,h,next);
        memcpy(h,next,32); cur/=2; width=(width+1)/2;
    }
    return memcmp(h,t->h[t->nlevels-1][0],32)==0;
}
static int verify_quaternary_index(const Input *in,const Tree *t,uint32_t index){
    unsigned char h[32]; desc_leaf(index,in->control[index],in->blob[index],in->blob_len[index],h);
    uint32_t cur=index,width=in->count;
    for(uint32_t level=0;width>1;level++){
        uint32_t start=(cur/4)*4,cc=width-start; if(cc>4)cc=4,cc=4;
        unsigned char children[MAX_COUNT][32];
        for(uint32_t j=0;j<cc;j++){
            uint32_t absolute=start+j;
            if(absolute==cur)memcpy(children[j],h,32); else memcpy(children[j],t->h[level][absolute],32);
        }
        unsigned char next[32]; qparent(level+1,cc,children,next); memcpy(h,next,32);
        cur/=4; width=(width+3)/4;
    }
    return memcmp(h,t->h[t->nlevels-1][0],32)==0;
}
static int verify_binary_all(const Input *in,const Tree *t){for(uint32_t i=0;i<in->count;i++)if(!verify_binary_index(in,t,i))return 0;return 1;}
static int verify_quaternary_all(const Input *in,const Tree *t){for(uint32_t i=0;i<in->count;i++)if(!verify_quaternary_index(in,t,i))return 0;return 1;}

static void hex32(const unsigned char h[32],char out[65]){static const char x[]="0123456789abcdef";for(int i=0;i<32;i++){out[2*i]=x[h[i]>>4];out[2*i+1]=x[h[i]&15];}out[64]=0;}

static Input load(const char *path){
    Input in; memset(&in,0,sizeof(in)); FILE *f=fopen(path,"rb"); if(!f){perror("open");exit(3);}
    in.count=rd32(f); if(in.count<1||in.count>MAX_COUNT){fprintf(stderr,"bad count\n");exit(3);}
    for(uint32_t i=0;i<in.count;i++){
        in.blob_len[i]=rd32(f); if(fread(in.control[i],1,CONTROL_BYTES,f)!=CONTROL_BYTES){fprintf(stderr,"short control\n");exit(3);}
        in.blob[i]=malloc(in.blob_len[i]?in.blob_len[i]:1); if(!in.blob[i])exit(4);
        if(in.blob_len[i]&&fread(in.blob[i],1,in.blob_len[i],f)!=in.blob_len[i]){fprintf(stderr,"short blob\n");exit(3);}
    }
    if(fgetc(f)!=EOF){fprintf(stderr,"trailing input\n");exit(3);} fclose(f); return in;
}
static void release(Input *in){for(uint32_t i=0;i<in->count;i++)free(in->blob[i]);}

int main(int argc,char **argv){
    if(argc!=4){fprintf(stderr,"usage: %s input reps inner\n",argv[0]);return 2;}
    int reps=atoi(argv[2]),inner=atoi(argv[3]); if(reps<5||inner<1)return 2;
    Input in=load(argv[1]); Tree bt,qt; build_binary(&in,&bt); build_quaternary(&in,&qt);
    if(!verify_binary_all(&in,&bt)||!verify_quaternary_all(&in,&qt)){fprintf(stderr,"self verify failed\n");return 5;}
    uint64_t *bb=malloc(sizeof(uint64_t)*reps),*qb=malloc(sizeof(uint64_t)*reps),*bv=malloc(sizeof(uint64_t)*reps),*qv=malloc(sizeof(uint64_t)*reps);
    if(!bb||!qb||!bv||!qv)return 4;
    for(int warm=0;warm<3;warm++){build_binary(&in,&bt);build_quaternary(&in,&qt);verify_binary_all(&in,&bt);verify_quaternary_all(&in,&qt);}
    for(int r=0;r<reps;r++){
        uint64_t a,b;
        if((r&1)==0){
            a=ns();for(int k=0;k<inner;k++){build_binary(&in,&bt);sink_byte^=bt.h[bt.nlevels-1][0][0];}bb[r]=ns()-a;
            a=ns();for(int k=0;k<inner;k++){build_quaternary(&in,&qt);sink_byte^=qt.h[qt.nlevels-1][0][0];}qb[r]=ns()-a;
            a=ns();for(int k=0;k<inner;k++)sink_byte^=(unsigned char)verify_binary_all(&in,&bt);bv[r]=ns()-a;
            a=ns();for(int k=0;k<inner;k++)sink_byte^=(unsigned char)verify_quaternary_all(&in,&qt);qv[r]=ns()-a;
        }else{
            a=ns();for(int k=0;k<inner;k++){build_quaternary(&in,&qt);sink_byte^=qt.h[qt.nlevels-1][0][0];}qb[r]=ns()-a;
            a=ns();for(int k=0;k<inner;k++){build_binary(&in,&bt);sink_byte^=bt.h[bt.nlevels-1][0][0];}bb[r]=ns()-a;
            a=ns();for(int k=0;k<inner;k++)sink_byte^=(unsigned char)verify_quaternary_all(&in,&qt);qv[r]=ns()-a;
            a=ns();for(int k=0;k<inner;k++)sink_byte^=(unsigned char)verify_binary_all(&in,&bt);bv[r]=ns()-a;
        }
    }
    qsort(bb,reps,sizeof(uint64_t),cmp_u64);qsort(qb,reps,sizeof(uint64_t),cmp_u64);qsort(bv,reps,sizeof(uint64_t),cmp_u64);qsort(qv,reps,sizeof(uint64_t),cmp_u64);
    char br[65],qr[65];hex32(bt.h[bt.nlevels-1][0],br);hex32(qt.h[qt.nlevels-1][0],qr);
    uint64_t mb=bb[reps/2],mq=qb[reps/2],mvb=bv[reps/2],mvq=qv[reps/2];
    printf("{\"count\":%u,\"reps\":%d,\"inner\":%d,\"binary_root\":\"%s\",\"quaternary_root\":\"%s\",\"binary_build_median_ns\":%llu,\"quaternary_build_median_ns\":%llu,\"build_ratio\":%.9f,\"binary_verify_all_median_ns\":%llu,\"quaternary_verify_all_median_ns\":%llu,\"verify_ratio\":%.9f}\n",in.count,reps,inner,br,qr,(unsigned long long)mb,(unsigned long long)mq,(double)mq/(double)mb,(unsigned long long)mvb,(unsigned long long)mvq,(double)mvq/(double)mvb);
    free(bb);free(qb);free(bv);free(qv);release(&in);return 0;
}
