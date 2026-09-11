#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define LOCAL_CAP 64u
#define HASH_CAP 128u
#define WINDOW 64u

typedef struct { uint64_t key; size_t start; int used; } ring_entry;
typedef struct { uint64_t key; uint8_t slot; uint8_t state; uint8_t pad[6]; } hash_bucket;
typedef struct {
    uint64_t lookup_events, hits, probes, tombstones_created, rebuilds, max_probe;
    uint64_t live_entries, decision_checksum, state_bytes;
} local_index_result;

static uint64_t mix64(uint64_t x) {
    x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);
    x ^= x >> 31; return x;
}
static uint64_t now_ns(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}
static void decision(local_index_result *o, int hit, size_t prior) {
    uint64_t v = hit ? (UINT64_C(0x9e3779b97f4a7c15) ^ (uint64_t)prior) : UINT64_C(0xd1b54a32d192ed03);
    o->decision_checksum ^= v + UINT64_C(0x9e3779b97f4a7c15) + (o->decision_checksum << 6) + (o->decision_checksum >> 2);
}
static void note_probe(local_index_result *o, uint64_t local) {
    o->probes++; if (local > o->max_probe) o->max_probe = local;
}

static int linear_find(const ring_entry r[LOCAL_CAP], size_t count, size_t head,
                       uint64_t key, size_t *prior, local_index_result *o) {
    for (size_t i=0;i<count;i++) {
        size_t s=(head+i)%LOCAL_CAP; o->probes++;
        if (r[s].used && r[s].key==key) { *prior=r[s].start; return 1; }
    }
    return 0;
}

/* 1 hit, 0 absent with empty sentinel, 2 absent after full-table scan, <0 corruption. */
static int hfind(const hash_bucket t[HASH_CAP], const ring_entry r[LOCAL_CAP],
                 uint64_t key, size_t *prior, size_t *slot, local_index_result *o) {
    size_t base=(size_t)(mix64(key)&(HASH_CAP-1u));
    for (size_t i=0;i<HASH_CAP;i++) {
        size_t b=(base+i)&(HASH_CAP-1u); note_probe(o,(uint64_t)i+1);
        if (t[b].state==0) return 0;
        if (t[b].state==1 && t[b].key==key) {
            size_t s=t[b].slot;
            if (s>=LOCAL_CAP || !r[s].used || r[s].key!=key) return -1;
            *prior=r[s].start; if(slot)*slot=s; return 1;
        }
    }
    return 2;
}
static int hinsert(hash_bucket t[HASH_CAP], uint64_t key, size_t slot, local_index_result *o) {
    size_t base=(size_t)(mix64(key)&(HASH_CAP-1u)), tomb=HASH_CAP;
    for(size_t i=0;i<HASH_CAP;i++) {
        size_t b=(base+i)&(HASH_CAP-1u); note_probe(o,(uint64_t)i+1);
        if(t[b].state==1 && t[b].key==key) return -1;
        if(t[b].state==2 && tomb==HASH_CAP) tomb=b;
        if(t[b].state==0) {
            size_t d=tomb!=HASH_CAP?tomb:b;
            t[d].key=key; t[d].slot=(uint8_t)slot; t[d].state=1; return 0;
        }
    }
    if(tomb!=HASH_CAP) { t[tomb].key=key; t[tomb].slot=(uint8_t)slot; t[tomb].state=1; return 0; }
    return -2;
}
static int hremove(hash_bucket t[HASH_CAP], uint64_t key, size_t slot, local_index_result *o) {
    size_t base=(size_t)(mix64(key)&(HASH_CAP-1u));
    for(size_t i=0;i<HASH_CAP;i++) {
        size_t b=(base+i)&(HASH_CAP-1u); note_probe(o,(uint64_t)i+1);
        if(t[b].state==0) return -1;
        if(t[b].state==1 && t[b].key==key && (size_t)t[b].slot==slot) { t[b].state=2; o->tombstones_created++; return 0; }
    }
    return -2;
}
static int rebuild(hash_bucket t[HASH_CAP], const ring_entry r[LOCAL_CAP], size_t count, size_t head, local_index_result *o) {
    memset(t,0,sizeof(hash_bucket)*HASH_CAP); o->rebuilds++;
    for(size_t i=0;i<count;i++) {
        size_t s=(head+i)%LOCAL_CAP;
        if(!r[s].used || hinsert(t,r[s].key,s,o)!=0) return -1;
    }
    return 0;
}

static int linear_event(ring_entry r[LOCAL_CAP], size_t *count, size_t *head,
                        uint64_t key, size_t start, local_index_result *o) {
    size_t prior=0; int hit=linear_find(r,*count,*head,key,&prior,o);
    o->lookup_events++; if(hit)o->hits++; decision(o,hit,prior);
    if(!hit) {
        size_t s;
        if(*count<LOCAL_CAP){s=(*head+*count)%LOCAL_CAP;(*count)++;}
        else{s=*head;*head=(*head+1)%LOCAL_CAP;}
        r[s].key=key;r[s].start=start;r[s].used=1;
    }
    o->live_entries=*count; return 0;
}
static int hash_event(ring_entry r[LOCAL_CAP], hash_bucket t[HASH_CAP], size_t *count, size_t *head,
                      uint64_t key, size_t start, local_index_result *o) {
    size_t prior=0,seen=0; int hit=hfind(t,r,key,&prior,&seen,o);
    if(hit==2) {
        if(rebuild(t,r,*count,*head,o)!=0) return -20;
        hit=hfind(t,r,key,&prior,&seen,o);
    }
    if(hit<0 || hit==2) return -21;
    o->lookup_events++; if(hit)o->hits++; decision(o,hit,prior);
    if(!hit) {
        size_t s;
        if(*count<LOCAL_CAP){s=(*head+*count)%LOCAL_CAP;(*count)++;}
        else {
            s=*head; uint64_t old=r[s].key;
            if(hremove(t,old,s,o)!=0) return -22;
            *head=(*head+1)%LOCAL_CAP;
        }
        r[s].key=key;r[s].start=start;r[s].used=1;
        if(hinsert(t,key,s,o)!=0) return -23;
    }
    o->live_entries=*count; return 0;
}

static int scan_linear(const uint8_t *d,size_t n,const uint64_t g[256],local_index_result *o){
    ring_entry r[LOCAL_CAP]={{0}};size_t count=0,head=0;uint64_t h=0;uint8_t rv=n?d[0]:0;size_t rl=0;
    *o=(local_index_result){0};o->state_bytes=sizeof(r);
    for(size_t p=0;p<n;p++){uint8_t v=d[p];if(!rl){rv=v;rl=1;}else if(v==rv)rl++;else{rv=v;rl=1;}h=(h<<1)+g[v];
        if(p+1<WINDOW||rl>=WINDOW||((p+1)%WINDOW)!=0)continue;
        if(linear_event(r,&count,&head,h,p+1-WINDOW,o)!=0)return -1;}
    return 0;
}
static int scan_hash(const uint8_t *d,size_t n,const uint64_t g[256],local_index_result *o){
    ring_entry r[LOCAL_CAP]={{0}};hash_bucket t[HASH_CAP]={{0}};size_t count=0,head=0;uint64_t h=0;uint8_t rv=n?d[0]:0;size_t rl=0;
    *o=(local_index_result){0};o->state_bytes=sizeof(r)+sizeof(t);
    for(size_t p=0;p<n;p++){uint8_t v=d[p];if(!rl){rv=v;rl=1;}else if(v==rv)rl++;else{rv=v;rl=1;}h=(h<<1)+g[v];
        if(p+1<WINDOW||rl>=WINDOW||((p+1)%WINDOW)!=0)continue;
        if(hash_event(r,t,&count,&head,h,p+1-WINDOW,o)!=0)return -2;}
    return 0;
}

int one_g02_local_index_hash_audit(const uint8_t*d,size_t n,const uint64_t g[256],local_index_result*b,local_index_result*c){
    if((!d&&n)||!g||!b||!c)return -1;if(scan_linear(d,n,g,b)!=0)return -2;if(scan_hash(d,n,g,c)!=0)return -3;
    return (b->lookup_events==c->lookup_events&&b->hits==c->hits&&b->live_entries==c->live_entries&&b->decision_checksum==c->decision_checksum)?0:-4;
}
int one_g02_local_index_hash_key_stream_audit(const uint64_t*keys,size_t n,local_index_result*b,local_index_result*c){
    if((!keys&&n)||!b||!c)return -1;ring_entry br[LOCAL_CAP]={{0}},cr[LOCAL_CAP]={{0}};hash_bucket t[HASH_CAP]={{0}};size_t bc=0,bh=0,cc=0,ch=0;
    *b=(local_index_result){0};*c=(local_index_result){0};b->state_bytes=sizeof(br);c->state_bytes=sizeof(cr)+sizeof(t);
    for(size_t i=0;i<n;i++){if(linear_event(br,&bc,&bh,keys[i],i*WINDOW,b)!=0)return -2;if(hash_event(cr,t,&cc,&ch,keys[i],i*WINDOW,c)!=0)return -3;
        if(bc!=cc||b->hits!=c->hits||b->decision_checksum!=c->decision_checksum)return -4;}return 0;
}
int one_g02_local_index_hash_measure(const uint8_t*d,size_t n,const uint64_t g[256],size_t batch,double*bn,double*cn,local_index_result*b,local_index_result*c){
    if((!d&&n)||!g||!batch||!bn||!cn||!b||!c)return -1;local_index_result br={0},cr={0};if(one_g02_local_index_hash_audit(d,n,g,&br,&cr)!=0)return -2;
    uint64_t t,b1,b2,c1,c2;t=now_ns();for(size_t i=0;i<batch;i++)if(scan_linear(d,n,g,&br)!=0)return -3;b1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;i++)if(scan_hash(d,n,g,&cr)!=0)return -4;c1=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;i++)if(scan_hash(d,n,g,&cr)!=0)return -5;c2=now_ns()-t;
    t=now_ns();for(size_t i=0;i<batch;i++)if(scan_linear(d,n,g,&br)!=0)return -6;b2=now_ns()-t;
    *bn=((double)b1+(double)b2)/(2.0*(double)batch);*cn=((double)c1+(double)c2)/(2.0*(double)batch);*b=br;*c=cr;return 0;
}
