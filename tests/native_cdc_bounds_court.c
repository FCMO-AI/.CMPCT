/* J24N02: native CDC cumulative-end correctness court, linked against actual source.
 * This C harness deliberately has no dependency on the archive Reader/Builder.
 * Historical mode confirms the inherited overflowing implementation's failure.
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>

size_t cmpct_cdc_cut(const uint8_t *, size_t, size_t, size_t, size_t, uint64_t *, size_t);

#define CAP 8192
static uint64_t out[CAP];
static uint64_t other[CAP];
static uint8_t bytes[4096];
static unsigned long long checks = 0;

static int violation(const char *message, size_t n, size_t min, size_t avg, size_t max) {
    fprintf(stderr, "FAIL %s n=%zu min=%zu avg=%zu max=%zu\n", message, n, min, avg, max);
    return 1;
}

static int valid_ends(const uint64_t *ends, size_t count, size_t n, size_t min, size_t avg, size_t max) {
    if (!count || count > CAP) return violation("no cuts / capacity", n, min, avg, max);
    uint64_t previous = 0;
    for (size_t k = 0; k < count; ++k) {
        if (ends[k] <= previous || ends[k] > (uint64_t)n)
            return violation("nonmonotone or out-of-bounds end", n, min, avg, max);
        if (ends[k] - previous > max)
            return violation("chunk larger than max_size", n, min, avg, max);
        previous = ends[k];
    }
    if (previous != (uint64_t)n) return violation("incomplete logical partition", n, min, avg, max);
    ++checks;
    return 0;
}

static void fill(size_t n, unsigned seed) {
    uint32_t x = (uint32_t)(seed | 1u);
    for (size_t i = 0; i < n; ++i) {
        x ^= x << 13; x ^= x >> 17; x ^= x << 5;
        bytes[i] = (uint8_t)(x & 255u);
    }
}

static int golden(void) {
    const uint64_t expected[] = {2,5,8,11,14,17,20,23,25,28,30,33,36,39,42,45,48};
    for (size_t i = 0; i < 48; ++i)
        bytes[i] = (uint8_t)(((unsigned)i * 31u) ^ ((unsigned)i / 3u));
    const size_t c = cmpct_cdc_cut(bytes,48,1,2,48,out,CAP);
    if (c != sizeof(expected)/sizeof(expected[0]) ||
        memcmp(out,expected,sizeof(expected)) != 0)
        return violation("inherited 48-byte golden changed",48,1,2,48);
    return valid_ends(out,c,48,1,2,48);
}

static uint64_t fold(uint64_t hash, uint64_t value) {
    for (unsigned k=0;k<8;++k) {
        hash ^= (uint8_t)(value >> (8*k));
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

/* Ordinary input fingerprint must match the *compiled historical source*,
 * not a reimplementation of the algorithm or a rounded performance statistic.
 */
static int ordinary(void) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned seed=0; seed<256; ++seed) {
        size_t n = 64u + (seed * 73u) % 2017u;
        fill(n,seed*17u+101u);
        for (size_t avg=1; avg<=256; avg*=2) {
            size_t min = avg > 1 ? avg/2 : 1;
            for (unsigned scale=1; scale<=4; scale*=2) {
                const size_t max = avg*scale;
                size_t c = cmpct_cdc_cut(bytes,n,min,avg,max,out,CAP);
                if(valid_ends(out,c,n,min,avg,max))return 1;
                hash=fold(hash,(uint64_t)c);
                for (size_t k=0;k<c;++k)hash=fold(hash,out[k]);
            }
        }
    }
    printf("ORDINARY_SOURCE_EXACT fingerprint=%016llx observations=%llu\n",
        (unsigned long long)hash,checks);
    return 0;
}

/* max_size>=n is a capacity ceiling, not a request to wrap the current start.
 * For avg>n use max(avg,n) as the canonical otherwise-valid ceiling.
 */
static int extremes(void) {
    for (unsigned seed=0; seed<256; ++seed) {
        const size_t n = 1u + (seed*37u)%2039u;
        fill(n,seed*67u+1u);
        for (size_t avg=1; avg<=1024; avg*=2) {
            const size_t min = avg>=4 ? avg/4 : 1;
            const size_t canonical = n>avg?n:avg;
            const size_t base = cmpct_cdc_cut(bytes,n,min,avg,canonical,other,CAP);
            if (valid_ends(other,base,n,min,avg,canonical))return 1;
            for (size_t d=0; d<=64; d=d==0?1:d*2) {
                size_t max = SIZE_MAX-d;
                if (max < canonical)continue;
                size_t c = cmpct_cdc_cut(bytes,n,min,avg,max,out,CAP);
                if (valid_ends(out,c,n,min,avg,max))return 1;
                if (c != base || memcmp(out,other,c*sizeof(uint64_t))!=0)
                    return violation("max>=n not equivalent to bounded canonical",n,min,avg,max);
            }
        }
    }
    /* Exact historical reproducer, plus inputs near addition-overflow. */
    for (size_t i=0;i<48;++i)
        bytes[i]=(uint8_t)(((unsigned)i*31u)^((unsigned)i/3u));
    size_t c=cmpct_cdc_cut(bytes,48,1,2,SIZE_MAX,out,CAP);
    if(c!=17 || valid_ends(out,c,48,1,2,SIZE_MAX))return 1;

    /* Exhausted caller capacity must still report failure, not a partial partition. */
    fill(256,119);
    c=cmpct_cdc_cut(bytes,256,1,2,2,out,CAP);
    if(valid_ends(out,c,256,1,2,2))return 1;
    if(c>=2 && cmpct_cdc_cut(bytes,256,1,2,2,other,c-1)!=0)
        return violation("insufficient cap not rejected",256,1,2,2);

    if(cmpct_cdc_cut(NULL,48,1,2,48,out,CAP)!=0 ||
       cmpct_cdc_cut(bytes,48,1,2,48,NULL,CAP)!=0 ||
       cmpct_cdc_cut(bytes,48,0,2,48,out,CAP)!=0 ||
       cmpct_cdc_cut(bytes,48,2,1,48,out,CAP)!=0 ||
       cmpct_cdc_cut(bytes,48,1,3,48,out,CAP)!=0 ||
       cmpct_cdc_cut(bytes,48,1,2,1,out,CAP)!=0 ||
       cmpct_cdc_cut(bytes,48,1,2,48,out,0)!=0)
        return violation("invalid-parameter behavior changed",48,1,2,48);

    /* Valid, huge powers-of-two must terminate even for a tiny real buffer. */
    const size_t huge_avg = ((SIZE_MAX >> 1) + 1);
    c=cmpct_cdc_cut(bytes,48,huge_avg,huge_avg,SIZE_MAX,out,CAP);
    if(c!=1 || out[0]!=48)return violation("large avg/min bounded cut",48,huge_avg,huge_avg,SIZE_MAX);
    ++checks;
    printf("EXTREME_BOUNDARY_COURT PASS cases=%llu\n",checks);
    return 0;
}

static int parent_negative(void) {
    for (size_t i=0;i<48;++i)
        bytes[i]=(uint8_t)(((unsigned)i*31u)^((unsigned)i/3u));
    size_t c=cmpct_cdc_cut(bytes,48,1,2,SIZE_MAX,out,256);
    if(c!=0)return violation("historical defect unexpectedly absent",48,1,2,SIZE_MAX);
    puts("HISTORICAL_EXTREME_NEGATIVE confirmed (count=0 with max=SIZE_MAX)");
    return 0;
}

int main(int argc,char **argv) {
    if (argc!=2) {fputs("usage: court ordinary|candidate|parent\n",stderr);return 2;}
    if(golden())return 1;
    if(strcmp(argv[1],"ordinary")==0)return ordinary();
    if(strcmp(argv[1],"candidate")==0)return extremes();
    if(strcmp(argv[1],"parent")==0)return parent_negative();
    return 2;
}
