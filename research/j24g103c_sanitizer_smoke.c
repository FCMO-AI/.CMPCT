/* J24G103c research C cutpoint hostile checks; standalone under ASan/UBSan. */
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
extern size_t j24g103_scan_cuts(const unsigned char*,size_t,const uint64_t*,size_t,size_t*,size_t);
int main(void){
 uint64_t gear[256];for(size_t i=0;i<256;i++)gear[i]=(uint64_t)(i*347u+37u);
 const size_t sizes[]={0,1,1023,1024,2047,4096,16384,65536,1000001};
 for(size_t s=0;s<sizeof(sizes)/sizeof(sizes[0]);s++){
  size_t n=sizes[s];unsigned char*buf=malloc(n+1);assert(buf);
  for(size_t j=0;j<n;j++)buf[j]=(unsigned char)((j*41+7)&255);
  for(size_t k=0;k<2;k++){
   size_t target=k?16384:4096,cap=n/(target/4)+2;
   size_t *ends=malloc(cap*sizeof(size_t));assert(ends);
   size_t cnt=j24g103_scan_cuts(buf,n,gear,target,ends,cap);
   assert(cnt<cap);size_t cursor=0;
   for(size_t i=0;i<cnt;i++){assert(ends[i]>cursor&&ends[i]<=n);cursor=ends[i];}
   if(n>0)assert(cursor==n);else assert(cnt==0);
   if(n>0)assert(j24g103_scan_cuts(buf,n,gear,target,ends,0)==(size_t)-1);
   assert(j24g103_scan_cuts(buf,n,gear,12345,ends,cap)==(size_t)-1);
   assert(j24g103_scan_cuts(NULL,n,gear,target,ends,cap)==(size_t)-1);
   free(ends);
  }
  free(buf);
 }
 puts("ASAN_UBSAN_BOUNDED_CUTS_PASS 9_LENGTHS_2_TARGETS");
 return 0;
}
