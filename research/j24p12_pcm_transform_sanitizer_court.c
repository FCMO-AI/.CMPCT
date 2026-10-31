/* J24P12 sanitizer court. No CMPCT import or source changes. */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>
int pcm16_forward(const uint8_t*,uint8_t*,size_t,unsigned,unsigned,int);
int pcm16_inverse(const uint8_t*,uint8_t*,size_t,unsigned,unsigned,int);
static uint32_t state=20261101u;
static uint32_t rnd(void){ state^=state<<13;state^=state>>17;state^=state<<5;return state; }
int main(void){
    int tests=0;
    const size_t lens[]={0,1,2,3,7,8,15,31,64,257,1024};
    for(unsigned ch=1;ch<=8;ch++) for(unsigned order=0;order<=2;order++)for(int planes=0;planes<=1;planes++)for(unsigned li=0;li<sizeof(lens)/sizeof(lens[0]);li++)for(unsigned rep=0;rep<7;rep++){
        size_t frames=lens[li],n=frames*ch*2;
        uint8_t *a=malloc(n+32),*b=malloc(n+32),*c=malloc(n+32);
        if(!a||!b||!c)return 100;
        memset(a,0xA9,n+32);memset(b,0xB7,n+32);memset(c,0xC5,n+32);
        for(size_t i=0;i<n;i++)a[i]=(uint8_t)rnd();
        for(size_t i=n;i<n+32;i++)a[i]=0xA9;
        if(pcm16_forward(a,b,frames,ch,order,planes)!=0 || pcm16_inverse(b,c,frames,ch,order,planes)!=0)return 101;
        if(memcmp(a,c,n))return 102;
        for(size_t i=n;i<n+32;i++)if(a[i]!=0xA9||b[i]!=0xB7||c[i]!=0xC5)return 103;
        free(a);free(b);free(c);tests++;
    }
    uint8_t a[32]={0},b[32]={0};
    if(pcm16_forward(a,b,1,0,1,0)!=-1 || pcm16_inverse(a,b,1,9,1,0)!=-1)return 104;
    if(pcm16_forward(a,b,1,1,3,0)!=-1 || pcm16_inverse(NULL,b,1,1,0,1)!=-1)return 105;
    if(pcm16_forward(a,b,SIZE_MAX,1,2,1)!=-1 || pcm16_inverse(a,b,SIZE_MAX,8,0,0)!=-1)return 106;
    printf("PASS native sanitized reversible byte-identical cases=%d channels=1..8 orders=0..2 planes=0..1\n",tests);
    return 0;
}
