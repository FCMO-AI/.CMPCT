/* J24P12 research-only fixed PCM predictor, not a CMPCT codec or ABI.
 * Prereg: github.com/FCMO-AI/.CMPCT/issues/872 before this implementation.
 * No allocation, no external libraries, src and dst must not overlap.
 */
#include <stdint.h>
#include <stddef.h>

static int32_t signed16(uint32_t u) { return u >= 32768u ? (int32_t)u-65536 : (int32_t)u; }
static uint32_t zigzag(int32_t v) { return v<0 ? (uint32_t)(-2*v-1):(uint32_t)(2*v); }
static int32_t unzig(uint32_t u) { return (u&1u) ? -((int32_t)(u>>1)+1):(int32_t)(u>>1); }
static size_t pos(size_t frame,unsigned chan,unsigned b,unsigned nch,size_t frames,int planes){
    return planes ? ((size_t)chan*2u+(size_t)b)*frames+frame
                  : 2u*(frame*(size_t)nch+(size_t)chan)+(size_t)b;
}
/* Returns 0 on success, -1 on shape/order failure. Frames/channels validated before multiplication. */
int pcm16_forward(const uint8_t* src,uint8_t* dst,size_t frames,unsigned nch,unsigned order,int planes){
    if(!src||!dst||nch<1||nch>8||order>2||frames>SIZE_MAX/2u/nch)return -1;
    int32_t p[8]={0},q[8]={0};
    for(size_t f=0;f<frames;f++)for(unsigned c=0;c<nch;c++){
        size_t ix=2u*(f*(size_t)nch+c);
        uint32_t u=src[ix]|((uint32_t)src[ix+1]<<8);
        int32_t v=signed16(u),res=v;
        if(order==1)res=v-p[c];
        if(order==2)res=v-2*p[c]+q[c];
        q[c]=p[c];p[c]=v;
        uint32_t mod=(uint32_t)res&65535u;
        uint32_t mapped=order==0 ? mod:zigzag(signed16(mod));
        dst[pos(f,c,0,nch,frames,planes)]=(uint8_t)mapped;
        dst[pos(f,c,1,nch,frames,planes)]=(uint8_t)(mapped>>8);
    }
    return 0;
}
int pcm16_inverse(const uint8_t* src,uint8_t* dst,size_t frames,unsigned nch,unsigned order,int planes){
    if(!src||!dst||nch<1||nch>8||order>2||frames>SIZE_MAX/2u/nch)return -1;
    int32_t p[8]={0},q[8]={0};
    for(size_t f=0;f<frames;f++)for(unsigned c=0;c<nch;c++){
        uint32_t u=src[pos(f,c,0,nch,frames,planes)]|((uint32_t)src[pos(f,c,1,nch,frames,planes)]<<8);
        int32_t d=order==0 ? signed16(u):unzig(u);
        int32_t v=d;
        if(order==1)v=d+p[c];
        if(order==2)v=d+2*p[c]-q[c];
        int32_t mapped=signed16((uint32_t)v&65535u);
        q[c]=p[c];p[c]=mapped;
        size_t ix=2u*(f*(size_t)nch+c);
        dst[ix]=(uint8_t)mapped; dst[ix+1]=(uint8_t)((uint32_t)mapped>>8);
    }
    return 0;
}
