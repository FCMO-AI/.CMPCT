#define _POSIX_C_SOURCE 200809L
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define LEAF 112u
#define REPS 41
#define MAX_REPS 64

static volatile unsigned char sink_byte;

static uint64_t ns(clockid_t id) {
    struct timespec t;
    clock_gettime(id, &t);
    return (uint64_t)t.tv_sec * 1000000000ull + (uint64_t)t.tv_nsec;
}
static int cmp64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return x < y ? -1 : x > y;
}
static uint64_t med(uint64_t *x) {
    qsort(x, REPS, sizeof(uint64_t), cmp64);
    return x[REPS / 2];
}
static void le32(unsigned char *p, uint32_t x) {
    for (int i = 0; i < 4; i++) p[i] = (unsigned char)(x >> (8 * i));
}
static void le64(unsigned char *p, uint64_t x) {
    for (int i = 0; i < 8; i++) p[i] = (unsigned char)(x >> (8 * i));
}
static uint64_t xorshift(uint64_t *s) {
    uint64_t x = *s;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    return *s = x;
}
static size_t total_nodes(size_t total) {
    size_t w = (total + LEAF - 1) / LEAF;
    if (!w) w = 1;
    size_t n = w;
    while (w > 1) { w = (w + 1) / 2; n += w; }
    return n;
}

static void baseline_leaf(uint64_t idx, uint64_t total, const unsigned char *p, size_t n, unsigned char out[32]) {
    unsigned char meta[16];
    le64(meta, idx); le64(meta + 8, total);
    SHA256_CTX c;
    SHA256_Init(&c);
    SHA256_Update(&c, "ONE-L\0", 6);
    SHA256_Update(&c, meta, 16);
    SHA256_Update(&c, p, n);
    SHA256_Final(out, &c);
}
static void baseline_parent(uint32_t level, const unsigned char *l, const unsigned char *r, unsigned char out[32]) {
    unsigned char q[4]; le32(q, level);
    SHA256_CTX c;
    SHA256_Init(&c);
    SHA256_Update(&c, "ONE-P\0", 6);
    SHA256_Update(&c, q, 4);
    SHA256_Update(&c, l, 32);
    SHA256_Update(&c, r, 32);
    SHA256_Final(out, &c);
}
static void baseline_root(uint64_t total, const unsigned char top[32], unsigned char out[32]) {
    unsigned char m[12]; le64(m, total); le32(m + 8, LEAF);
    SHA256_CTX c;
    SHA256_Init(&c);
    SHA256_Update(&c, "ONE-R\0", 6);
    SHA256_Update(&c, m, 12);
    SHA256_Update(&c, top, 32);
    SHA256_Final(out, &c);
}

static int build_baseline(const unsigned char *data, size_t total, unsigned char root[32]) {
    size_t count = (total + LEAF - 1) / LEAF;
    if (!count) count = 1;
    size_t nodes = total_nodes(total);
    unsigned char *arena = (unsigned char *)malloc(nodes * 32);
    if (!arena) return 0;
    size_t cur_off = 0, next_off = count;
    for (size_t i = 0; i < count; i++) {
        size_t off = i * LEAF, n = off < total ? total - off : 0;
        if (n > LEAF) n = LEAF;
        baseline_leaf(i, total, data + off, n, arena + (cur_off + i) * 32);
    }
    size_t width = count; uint32_t level = 1;
    while (width > 1) {
        size_t nw = (width + 1) / 2;
        for (size_t i = 0; i < nw; i++) {
            const unsigned char *l = arena + (cur_off + 2 * i) * 32;
            const unsigned char *r = (2 * i + 1 < width) ? arena + (cur_off + 2 * i + 1) * 32 : l;
            baseline_parent(level, l, r, arena + (next_off + i) * 32);
        }
        cur_off = next_off; next_off += nw; width = nw; level++;
    }
    baseline_root(total, arena + cur_off * 32, root);
    sink_byte ^= arena[(nodes - 1) * 32];
    free(arena);
    return 1;
}

static int build_clone(const unsigned char *data, size_t total, unsigned char root[32]) {
    size_t count = (total + LEAF - 1) / LEAF;
    if (!count) count = 1;
    size_t nodes = total_nodes(total);
    unsigned char *arena = (unsigned char *)malloc(nodes * 32);
    if (!arena) return 0;
    size_t cur_off = 0, next_off = count;

    SHA256_CTX leaf_prefix;
    SHA256_Init(&leaf_prefix);
    SHA256_Update(&leaf_prefix, "ONE-L\0", 6);
    for (size_t i = 0; i < count; i++) {
        size_t off = i * LEAF, n = off < total ? total - off : 0;
        if (n > LEAF) n = LEAF;
        unsigned char meta[16]; le64(meta, i); le64(meta + 8, total);
        SHA256_CTX c = leaf_prefix;
        SHA256_Update(&c, meta, 16);
        SHA256_Update(&c, data + off, n);
        SHA256_Final(arena + (cur_off + i) * 32, &c);
    }

    size_t width = count; uint32_t level = 1;
    while (width > 1) {
        size_t nw = (width + 1) / 2;
        unsigned char q[4]; le32(q, level);
        SHA256_CTX parent_prefix;
        SHA256_Init(&parent_prefix);
        SHA256_Update(&parent_prefix, "ONE-P\0", 6);
        SHA256_Update(&parent_prefix, q, 4);
        for (size_t i = 0; i < nw; i++) {
            const unsigned char *l = arena + (cur_off + 2 * i) * 32;
            const unsigned char *r = (2 * i + 1 < width) ? arena + (cur_off + 2 * i + 1) * 32 : l;
            SHA256_CTX c = parent_prefix;
            SHA256_Update(&c, l, 32);
            SHA256_Update(&c, r, 32);
            SHA256_Final(arena + (next_off + i) * 32, &c);
        }
        cur_off = next_off; next_off += nw; width = nw; level++;
    }

    unsigned char m[12]; le64(m, total); le32(m + 8, LEAF);
    SHA256_CTX root_prefix;
    SHA256_Init(&root_prefix);
    SHA256_Update(&root_prefix, "ONE-R\0", 6);
    SHA256_Update(&root_prefix, m, 12);
    SHA256_CTX rc = root_prefix;
    SHA256_Update(&rc, arena + cur_off * 32, 32);
    SHA256_Final(root, &rc);
    sink_byte ^= arena[(nodes - 1) * 32];
    free(arena);
    return 1;
}

static void measure(int clone, const unsigned char *data, size_t total, uint64_t *wall, uint64_t *cpu, unsigned char root[32]) {
    uint64_t w0 = ns(CLOCK_MONOTONIC), c0 = ns(CLOCK_PROCESS_CPUTIME_ID);
    int ok = clone ? build_clone(data, total, root) : build_baseline(data, total, root);
    uint64_t c1 = ns(CLOCK_PROCESS_CPUTIME_ID), w1 = ns(CLOCK_MONOTONIC);
    if (!ok) { fprintf(stderr, "allocation failure\n"); exit(2); }
    *wall = w1 - w0; *cpu = c1 - c0;
}

int main(void) {
    const size_t sizes[] = {1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576};
    const size_t rows = sizeof(sizes)/sizeof(sizes[0]);
    int exact_failures = 0;
    double wall_ratios[11], cpu_ratios[11];
    printf("{\"schema\":\"cmpct-one-g02-auth-tree-prefix-state-clone-v1\",\"leaf_bytes\":%u,\"repetitions\":%d,\"candidate_added_staging_bytes\":0,\"candidate_prefix_workspace_bytes\":%zu,\"rows\":[", LEAF, REPS, 3 * sizeof(SHA256_CTX));
    for (size_t si = 0; si < rows; si++) {
        size_t n = sizes[si];
        unsigned char *data = (unsigned char *)malloc(n ? n : 1);
        if (!data) return 2;
        uint64_t seed = 0x9e3779b97f4a7c15ULL ^ (uint64_t)n;
        for (size_t i = 0; i < n; i++) data[i] = (unsigned char)xorshift(&seed);
        unsigned char br[32], cr[32];
        if (!build_baseline(data,n,br) || !build_clone(data,n,cr)) return 2;
        if (memcmp(br,cr,32) != 0) exact_failures++;
        uint64_t bw[MAX_REPS],bc[MAX_REPS],cw[MAX_REPS],cc[MAX_REPS];
        for (int r=0;r<REPS;r++) {
            unsigned char x[32], y[32]; uint64_t w,c;
            if (r & 1) {
                measure(1,data,n,&w,&c,x); cw[r]=w; cc[r]=c;
                measure(0,data,n,&w,&c,y); bw[r]=w; bc[r]=c;
            } else {
                measure(0,data,n,&w,&c,y); bw[r]=w; bc[r]=c;
                measure(1,data,n,&w,&c,x); cw[r]=w; cc[r]=c;
            }
            if (memcmp(x,y,32) != 0) exact_failures++;
        }
        uint64_t bwm=med(bw), bcm=med(bc), cwm=med(cw), ccm=med(cc);
        wall_ratios[si]=(double)cwm/(double)bwm; cpu_ratios[si]=(double)ccm/(double)bcm;
        if (si) printf(",");
        printf("{\"root_bytes\":%zu,\"node_count\":%zu,\"baseline_wall_median_ns\":%llu,\"candidate_wall_median_ns\":%llu,\"wall_ratio\":%.9f,\"baseline_cpu_median_ns\":%llu,\"candidate_cpu_median_ns\":%llu,\"cpu_ratio\":%.9f}",n,total_nodes(n),(unsigned long long)bwm,(unsigned long long)cwm,wall_ratios[si],(unsigned long long)bcm,(unsigned long long)ccm,cpu_ratios[si]);
        free(data);
    }
    double prod_wall[8], prod_cpu[8]; int k=0; double max_wall=0,max_cpu=0;
    int all_prod_wall=1;
    for (size_t i=0;i<rows;i++) {
        if (wall_ratios[i]>max_wall) max_wall=wall_ratios[i];
        if (cpu_ratios[i]>max_cpu) max_cpu=cpu_ratios[i];
        if (sizes[i]>=8192) {
            if (wall_ratios[i]>0.97) all_prod_wall=0;
            prod_wall[k]=wall_ratios[i]; prod_cpu[k]=cpu_ratios[i]; k++;
        }
    }
    /* k is 8 for the frozen grid. */
    for (int i=0;i<k;i++) for(int j=i+1;j<k;j++) {
        if (prod_wall[j]<prod_wall[i]) {double z=prod_wall[i];prod_wall[i]=prod_wall[j];prod_wall[j]=z;}
        if (prod_cpu[j]<prod_cpu[i]) {double z=prod_cpu[i];prod_cpu[i]=prod_cpu[j];prod_cpu[j]=z;}
    }
    double mw=(k&1)?prod_wall[k/2]:(prod_wall[k/2-1]+prod_wall[k/2])/2.0;
    double mc=(k&1)?prod_cpu[k/2]:(prod_cpu[k/2-1]+prod_cpu[k/2])/2.0;
    int pass = exact_failures==0 && all_prod_wall && mw<=0.92 && mc<=0.95 && max_wall<=1.05 && max_cpu<=1.05;
    printf("],\"exact_failures\":%d,\"productive_wall_median_ratio\":%.9f,\"productive_cpu_median_ratio\":%.9f,\"max_wall_ratio\":%.9f,\"max_cpu_ratio\":%.9f,\"decision\":\"%s\"}\n",exact_failures,mw,mc,max_wall,max_cpu,pass?"advance_prefix_state_clone":"prefix_state_clone_insufficient");
    return pass ? 0 : 1;
}
