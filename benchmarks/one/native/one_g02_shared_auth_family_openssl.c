#define _POSIX_C_SOURCE 200809L
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define VERSIONS 8
#define LEAF 80u
#define REQUEST 4096u
#define CONTROL 40u
#define MAX_LEVELS 16
#define REPS 11
#define INNER_READ 20
#define MAX_MUT 64

typedef struct { size_t width[MAX_LEVELS], levels; unsigned char *h[MAX_LEVELS]; size_t total; } Tree;
typedef struct { uint32_t pos; unsigned char val; } Diff;
typedef struct { Diff d[MAX_MUT]; uint32_t n; unsigned char *blob; size_t blob_n; unsigned char control[CONTROL]; } Desc;
static volatile unsigned char sink_byte;

static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec;}
static int cmp64(const void*a,const void*b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return x<y?-1:x>y;}
static void le32(unsigned char*p,uint32_t x){for(int i=0;i<4;i++)p[i]=(unsigned char)(x>>(8*i));}
static void le64(unsigned char*p,uint64_t x){for(int i=0;i<8;i++)p[i]=(unsigned char)(x>>(8*i));}
static uint64_t xorshift(uint64_t *s){uint64_t x=*s;x^=x<<13;x^=x>>7;x^=x<<17;return *s=x;}

static void leaf_hash(uint64_t idx,uint64_t total,const unsigned char*p,size_t n,unsigned char out[32]){
  unsigned char meta[16];le64(meta,idx);le64(meta+8,total);SHA256_CTX c;SHA256_Init(&c);SHA256_Update(&c,"ONE-L\0",6);SHA256_Update(&c,meta,16);SHA256_Update(&c,p,n);SHA256_Final(out,&c);
}
static void parent_hash(uint32_t level,const unsigned char*l,const unsigned char*r,unsigned char out[32]){
  unsigned char q[4];le32(q,level);SHA256_CTX c;SHA256_Init(&c);SHA256_Update(&c,"ONE-P\0",6);SHA256_Update(&c,q,4);SHA256_Update(&c,l,32);SHA256_Update(&c,r,32);SHA256_Final(out,&c);
}
static void root_commit(uint64_t total,uint32_t leaf,const unsigned char top[32],unsigned char out[32]){
  unsigned char m[12];le64(m,total);le32(m+8,leaf);SHA256_CTX c;SHA256_Init(&c);SHA256_Update(&c,"ONE-R\0",6);SHA256_Update(&c,m,12);SHA256_Update(&c,top,32);SHA256_Final(out,&c);
}
static int tree_build(const unsigned char*data,size_t total,Tree*t,unsigned char root[32]){
  memset(t,0,sizeof(*t));t->total=total;t->width[0]=(total+LEAF-1)/LEAF;if(!t->width[0])t->width[0]=1;t->levels=1;
  t->h[0]=malloc(t->width[0]*32);if(!t->h[0])return 0;
  for(size_t i=0;i<t->width[0];i++){size_t off=i*LEAF,n=off<total?total-off:0;if(n>LEAF)n=LEAF;leaf_hash(i,total,data+off,n,t->h[0]+i*32);}
  while(t->width[t->levels-1]>1){size_t p=t->levels-1,w=t->width[p],nw=(w+1)/2;t->width[t->levels]=nw;t->h[t->levels]=malloc(nw*32);if(!t->h[t->levels])return 0;for(size_t i=0;i<nw;i++){const unsigned char*l=t->h[p]+2*i*32;const unsigned char*r=(2*i+1<w)?t->h[p]+(2*i+1)*32:l;parent_hash((uint32_t)t->levels,l,r,t->h[t->levels]+i*32);}t->levels++;}
  root_commit(total,LEAF,t->h[t->levels-1],root);return 1;
}
static void tree_free(Tree*t){for(size_t i=0;i<t->levels;i++)free(t->h[i]);memset(t,0,sizeof(*t));}
static size_t tree_nonroot_bytes(const Tree*t){size_t nodes=0;for(size_t i=0;i<t->levels;i++)nodes+=t->width[i];return (nodes-1)*32;}

/* Recompute only the requested cone; stored hashes are used for disjoint siblings. */
static void cone_hash(const Tree*t,const unsigned char*data,size_t level,size_t node,size_t first,size_t last,unsigned char out[32]){
  if(level==0){size_t off=node*LEAF,n=off<t->total?t->total-off:0;if(n>LEAF)n=LEAF;leaf_hash(node,t->total,data+off,n,out);return;}
  size_t span=(size_t)1<<level, lo=node*span, hi=lo+span-1;
  if(hi<first||lo>last){memcpy(out,t->h[level]+node*32,32);return;}
  size_t pw=t->width[level-1],li=node*2,ri=li+1;unsigned char l[32],r[32];
  cone_hash(t,data,level-1,li,first,last,l);
  if(ri<pw)cone_hash(t,data,level-1,ri,first,last,r);else memcpy(r,l,32);
  parent_hash((uint32_t)level,l,r,out);
}
static int verify_range(const Tree*t,const unsigned char*data,const unsigned char root[32],size_t start,size_t len){
  size_t first=start/LEAF,last=(start+len-1)/LEAF;unsigned char top[32],got[32];cone_hash(t,data,t->levels-1,0,first,last,top);root_commit(t->total,LEAF,top,got);return memcmp(got,root,32)==0;
}

static size_t uleb(unsigned char*out,uint32_t n){size_t k=0;do{unsigned char b=n&127;n>>=7;if(n)b|=128;out[k++]=b;}while(n);return k;}
static void make_desc(const unsigned char*base,unsigned char*edited,size_t n,uint64_t seed,uint32_t muts,uint32_t version,Desc*d){
  memcpy(edited,base,n);memset(d,0,sizeof(*d));uint64_t s=seed^(0x9e3779b97f4a7c15ULL*(version+1));
  for(uint32_t i=0;i<muts;i++){uint32_t p=(uint32_t)(xorshift(&s)%n);unsigned char v=(unsigned char)xorshift(&s);if(v==edited[p])v^=0x5a;edited[p]=v;d->d[d->n].pos=p;d->d[d->n].val=v;d->n++;}
  /* Sort and coalesce duplicate positions so Surprise remains exact. */
  for(uint32_t i=0;i<d->n;i++)for(uint32_t j=i+1;j<d->n;j++)if(d->d[j].pos<d->d[i].pos){Diff z=d->d[i];d->d[i]=d->d[j];d->d[j]=z;}
  uint32_t w=0;for(uint32_t i=0;i<d->n;i++){if(w&&d->d[w-1].pos==d->d[i].pos)d->d[w-1]=d->d[i];else d->d[w++]=d->d[i];}d->n=w;
  d->blob=malloc(1+d->n*6);size_t k=uleb(d->blob,d->n);uint32_t prev=0;for(uint32_t i=0;i<d->n;i++){k+=uleb(d->blob+k,d->d[i].pos-prev);d->blob[k++]=d->d[i].val;prev=d->d[i].pos;}d->blob_n=k;
  memset(d->control,0,CONTROL);memcpy(d->control,"ONE-TRANSLATION-LAW",19);le32(d->control+32,version);le32(d->control+36,(uint32_t)n);
}
static void desc_free(Desc*d){free(d->blob);}
static void desc_leaf(uint32_t idx,const Desc*d,unsigned char out[32]){unsigned char sd[32],i4[4];SHA256(d->blob,d->blob_n,sd);le32(i4,idx);SHA256_CTX c;SHA256_Init(&c);SHA256_Update(&c,"ONE-GDESC-L\0",12);SHA256_Update(&c,i4,4);SHA256_Update(&c,d->control,CONTROL);SHA256_Update(&c,sd,32);SHA256_Final(out,&c);}
static void qparent(uint32_t level,uint32_t count,const unsigned char child[4][32],unsigned char out[32]){unsigned char m[8];le32(m,level);le32(m+4,count);SHA256_CTX c;SHA256_Init(&c);SHA256_Update(&c,"ONE-GDESC-QP\0",13);SHA256_Update(&c,m,8);for(uint32_t i=0;i<count;i++)SHA256_Update(&c,child[i],32);SHA256_Final(out,&c);}
typedef struct{unsigned char leaf[VERSIONS][32],p0[2][32],root[32];}QTree;
static void qbuild(const Desc d[VERSIONS],QTree*q){for(uint32_t i=0;i<VERSIONS;i++)desc_leaf(i,&d[i],q->leaf[i]);for(uint32_t p=0;p<2;p++){unsigned char c[4][32];for(int j=0;j<4;j++)memcpy(c[j],q->leaf[p*4+j],32);qparent(1,4,c,q->p0[p]);}unsigned char c[4][32];memcpy(c[0],q->p0[0],32);memcpy(c[1],q->p0[1],32);qparent(2,2,c,q->root);}
static int qverify(const Desc d[VERSIONS],const QTree*q,uint32_t idx){unsigned char h[32],c[4][32],p[32],root[32];desc_leaf(idx,&d[idx],h);uint32_t group=idx/4;for(int j=0;j<4;j++)memcpy(c[j],q->leaf[group*4+j],32);memcpy(c[idx%4],h,32);qparent(1,4,c,p);memcpy(c[0],q->p0[0],32);memcpy(c[1],q->p0[1],32);memcpy(c[group],p,32);qparent(2,2,c,root);return memcmp(root,q->root,32)==0;}
static void apply(unsigned char*out,const unsigned char*base,size_t start,const Desc*d){memcpy(out,base+start,REQUEST);size_t end=start+REQUEST;for(uint32_t i=0;i<d->n;i++)if(d->d[i].pos>=start&&d->d[i].pos<end)out[d->d[i].pos-start]=d->d[i].val;}

static uint64_t med(uint64_t x[REPS]){qsort(x,REPS,sizeof(uint64_t),cmp64);return x[REPS/2];}
int main(void){
  const size_t sizes[2]={65536,262144};double br[6],rr[6];int row=0,exact_fail=0,corrupt_fail=0;
  printf("{\"schema\":\"cmpct-one-g02-native-shared-auth-family-v1\",\"rows\":[");
  for(int si=0;si<2;si++)for(int fi=0;fi<3;fi++){
    size_t n=sizes[si],start=((n-REQUEST)/2/LEAF)*LEAF+37;unsigned char*base=malloc(n);unsigned char*edited[VERSIONS];Desc d[VERSIONS];uint64_t seed=0xC0DEC0FFEEULL^(uint64_t)n^(uint64_t)(fi+1)*0xD1B54A32D192ED03ULL,s=seed;
    for(size_t i=0;i<n;i++)base[i]=(unsigned char)xorshift(&s);for(int v=0;v<VERSIONS;v++){edited[v]=malloc(n);uint32_t muts=1u<<(2*(v%4));make_desc(base,edited[v],n,seed,muts,(uint32_t)v,&d[v]);}
    Tree it[VERSIONS+1],bt;unsigned char ir[VERSIONS+1][32],brt[32];QTree q;
    tree_build(base,n,&it[0],ir[0]);for(int v=0;v<VERSIONS;v++)tree_build(edited[v],n,&it[v+1],ir[v+1]);tree_build(base,n,&bt,brt);qbuild(d,&q);
    uint64_t ti[REPS],ts[REPS],ri[REPS],rs[REPS];
    for(int r=0;r<REPS;r++){
      uint64_t a=ns();for(int z=0;z<3;z++){Tree x;unsigned char rr0[32];tree_build(base,n,&x,rr0);tree_free(&x);for(int v=0;v<VERSIONS;v++){tree_build(edited[v],n,&x,rr0);tree_free(&x);}}ti[r]=ns()-a;
      a=ns();for(int z=0;z<3;z++){Tree x;unsigned char rr0[32];QTree qq;tree_build(base,n,&x,rr0);qbuild(d,&qq);sink_byte^=qq.root[0];tree_free(&x);}ts[r]=ns()-a;
      a=ns();for(int k=0;k<INNER_READ;k++)for(int v=0;v<VERSIONS;v++)sink_byte^=(unsigned char)verify_range(&it[v+1],edited[v],ir[v+1],start,REQUEST);ri[r]=ns()-a;
      unsigned char out[REQUEST];a=ns();for(int k=0;k<INNER_READ;k++)for(int v=0;v<VERSIONS;v++){int ok=verify_range(&bt,base,brt,start,REQUEST)&&qverify(d,&q,(uint32_t)v);apply(out,base,start,&d[v]);if(memcmp(out,edited[v]+start,REQUEST)!=0)ok=0;sink_byte^=(unsigned char)ok;}rs[r]=ns()-a;
    }
    uint64_t mib=med(ti),msb=med(ts),mir=med(ri),msr=med(rs);br[row]=(double)msb/mib;rr[row]=(double)msr/mir;
    for(int v=0;v<VERSIONS;v++){unsigned char out[REQUEST];int ok=verify_range(&bt,base,brt,start,REQUEST)&&qverify(d,&q,(uint32_t)v);apply(out,base,start,&d[v]);if(!ok||memcmp(out,edited[v]+start,REQUEST)!=0)exact_fail++;}
    unsigned char saved=base[start];base[start]^=1;if(verify_range(&bt,base,brt,start,REQUEST))corrupt_fail++;base[start]=saved;
    unsigned char savedb=d[0].blob[d[0].blob_n-1];d[0].blob[d[0].blob_n-1]^=1;if(qverify(d,&q,0))corrupt_fail++;d[0].blob[d[0].blob_n-1]=savedb;
    size_t ind_persist=0;for(int v=0;v<VERSIONS+1;v++)ind_persist+=n+tree_nonroot_bytes(&it[v]);size_t shared_persist=n+tree_nonroot_bytes(&bt)+8+VERSIONS*CONTROL+2*32;for(int v=0;v<VERSIONS;v++)shared_persist+=d[v].blob_n;
    if(row)printf(",");printf("{\"root_bytes\":%zu,\"family\":%d,\"independent_persisted_bytes\":%zu,\"shared_persisted_bytes\":%zu,\"persisted_ratio\":%.9f,\"independent_build_median_ns\":%llu,\"shared_build_median_ns\":%llu,\"build_ratio\":%.9f,\"independent_read_median_ns\":%llu,\"shared_read_median_ns\":%llu,\"read_ratio\":%.9f}",n,fi,ind_persist,shared_persist,(double)shared_persist/ind_persist,(unsigned long long)mib,(unsigned long long)msb,br[row],(unsigned long long)mir,(unsigned long long)msr,rr[row]);
    for(int v=0;v<VERSIONS;v++){tree_free(&it[v+1]);free(edited[v]);desc_free(&d[v]);}tree_free(&it[0]);tree_free(&bt);free(base);row++;
  }
  double maxb=0,maxr=0;for(int i=0;i<6;i++){if(br[i]>maxb)maxb=br[i];if(rr[i]>maxr)maxr=rr[i];}qsort(br,6,sizeof(double),(int(*)(const void*,const void*))cmp64); /* medians reported by driver-free max gate below */
  int pass=exact_fail==0&&corrupt_fail==0&&maxb<=0.20&&maxr<=1.20;
  printf("],\"exact_failures\":%d,\"corruption_failures\":%d,\"max_build_ratio\":%.9f,\"max_read_ratio\":%.9f,\"decision\":\"%s\",\"claim_boundary\":\"independent native OpenSSL transfer corpus; no discovery cost, canonical wire, product, comparator, or release authority\"}\n",exact_fail,corrupt_fail,maxb,maxr,pass?"advance_native_shared_auth_family":"native_shared_auth_family_debt");
  return pass?0:1;
}
