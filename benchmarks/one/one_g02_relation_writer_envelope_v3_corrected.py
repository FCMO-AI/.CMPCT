"""Admissible correction of ONE-G0.2 relation writer envelope V3.

Only correction versus the invalid initial V3 source: lane0 is the charged seed pair,
so the native pre-gate truly reads exactly three source/target pairs per 64-byte block.
All matrix cases and decision thresholds remain inherited unchanged.
"""
from __future__ import annotations

import benchmarks.one.one_g02_relation_writer_envelope_v3 as v3

_CORRECTED_GATE_C = r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct { uint32_t op, value; uint64_t eligible, votes, probe_bytes; } gate_out;
static uint64_t mix64(uint64_t x) {
    x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}
int paired_triplet_gate(const uint8_t *a,const uint8_t *b,size_t n,gate_out *out) {
    if (!out || (n && (!a || !b))) return 2;
    memset(out,0,sizeof(*out));
    uint64_t ah[256]={0},xh[256]={0};
    const size_t blocks=n/64u;
    out->eligible=blocks;
    for(size_t bi=0;bi<blocks;++bi){
        const size_t base=bi*64u;
        const size_t l0=0u;
        uint64_t s=mix64(((uint64_t)a[base]<<8) ^ b[base] ^ (uint64_t)bi);
        const size_t l1=1u+(size_t)(s%63u);
        s=mix64(s+UINT64_C(0x9e3779b97f4a7c15));
        const size_t l2=1u+(size_t)(s%63u);
        const size_t lanes[3]={l0,l1,l2};
        uint8_t ad[3],xv[3];
        for(unsigned k=0;k<3;++k){
            const size_t p=base+lanes[k];
            ad[k]=(uint8_t)(b[p]-a[p]);
            xv[k]=(uint8_t)(b[p]^a[p]);
        }
        out->probe_bytes += 6;
        if(ad[0]!=0 && ad[0]==ad[1] && ad[1]==ad[2]) ++ah[ad[0]];
        if(xv[0]!=0 && xv[0]==xv[1] && xv[1]==xv[2]) ++xh[xv[0]];
    }
    uint64_t ab=0,xb=0; uint32_t ai=0,xi=0;
    for(uint32_t i=1;i<256;++i){
        if(ah[i]>ab){ab=ah[i];ai=i;}
        if(xh[i]>xb){xb=xh[i];xi=i;}
    }
    const int aok=blocks>=8 && ai && ab*8>=blocks*7;
    const int xok=blocks>=8 && xi && xb*8>=blocks*7;
    if(aok && (!xok || ab>=xb)){out->op=1;out->value=ai;out->votes=ab;}
    else if(xok){out->op=2;out->value=xi;out->votes=xb;}
    return 0;
}
'''

v3._GATE_C = _CORRECTED_GATE_C
v3._gate_lib.cache_clear()

if __name__ == "__main__":
    raise SystemExit(v3.run())
