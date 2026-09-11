#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <openssl/sha.h>

static const uint8_t LEAF_DOMAIN[6] = {'O','N','E','-','L',0};
static const uint8_t PARENT_DOMAIN[6] = {'O','N','E','-','P',0};
static const uint8_t ROOT_DOMAIN[6] = {'O','N','E','-','R',0};

static void le32(uint8_t out[4], uint32_t v) {
    out[0]=(uint8_t)v; out[1]=(uint8_t)(v>>8); out[2]=(uint8_t)(v>>16); out[3]=(uint8_t)(v>>24);
}
static void le64(uint8_t out[8], uint64_t v) {
    for (unsigned i=0;i<8;i++) out[i]=(uint8_t)(v>>(8*i));
}
static int hash_parts(const uint8_t *a,size_t an,const uint8_t *b,size_t bn,const uint8_t *c,size_t cn,uint8_t out[32]) {
    SHA256_CTX ctx;
    if (!SHA256_Init(&ctx)) return 0;
    if (an && !SHA256_Update(&ctx,a,an)) return 0;
    if (bn && !SHA256_Update(&ctx,b,bn)) return 0;
    if (cn && !SHA256_Update(&ctx,c,cn)) return 0;
    return SHA256_Final(out,&ctx) == 1;
}

/*
 * Exact native builder for experiments.one.auth_tree.
 * out_nodes stores every tree digest in level order: leaves first, then each parent level,
 * including the final one-node tree root. out_root is the separately domain-committed root.
 * Returns 0 on success, -1 invalid arguments, -2 insufficient output capacity, -3 SHA failure.
 */
int one_auth_tree_native(
    const uint8_t *data, size_t data_len, uint32_t leaf_bytes,
    uint8_t *out_nodes, size_t node_capacity, size_t *out_node_count,
    uint8_t out_root[32]
) {
    if (!leaf_bytes || !out_nodes || !out_node_count || !out_root || (data_len && !data)) return -1;
    size_t leaves = data_len ? (data_len + (size_t)leaf_bytes - 1) / (size_t)leaf_bytes : 1;
    size_t total_nodes = 0, width = leaves;
    while (1) {
        if (SIZE_MAX - total_nodes < width) return -1;
        total_nodes += width;
        if (width == 1) break;
        width = (width + 1) / 2;
    }
    if (node_capacity < total_nodes) return -2;

    uint8_t meta16[16];
    le64(meta16 + 8, (uint64_t)data_len);
    for (size_t i=0;i<leaves;i++) {
        le64(meta16, (uint64_t)i);
        size_t start = i * (size_t)leaf_bytes;
        size_t n = 0;
        if (start < data_len) {
            n = data_len - start;
            if (n > leaf_bytes) n = leaf_bytes;
        }
        if (!hash_parts(LEAF_DOMAIN,6,meta16,16,n ? data+start : NULL,n,out_nodes + i*32)) return -3;
    }

    size_t prev_off = 0, write_off = leaves;
    width = leaves;
    uint32_t level = 1;
    while (width > 1) {
        size_t next_width = (width + 1) / 2;
        uint8_t meta4[4]; le32(meta4, level);
        for (size_t j=0;j<next_width;j++) {
            const uint8_t *left = out_nodes + (prev_off + 2*j)*32;
            const uint8_t *right = (2*j+1 < width) ? out_nodes + (prev_off + 2*j+1)*32 : left;
            SHA256_CTX ctx;
            if (!SHA256_Init(&ctx) || !SHA256_Update(&ctx,PARENT_DOMAIN,6) ||
                !SHA256_Update(&ctx,meta4,4) || !SHA256_Update(&ctx,left,32) ||
                !SHA256_Update(&ctx,right,32) || !SHA256_Final(out_nodes + (write_off+j)*32,&ctx)) return -3;
        }
        prev_off = write_off;
        write_off += next_width;
        width = next_width;
        level++;
    }

    uint8_t rootmeta[12];
    le64(rootmeta,(uint64_t)data_len); le32(rootmeta+8,leaf_bytes);
    const uint8_t *tree_root = out_nodes + (total_nodes-1)*32;
    if (!hash_parts(ROOT_DOMAIN,6,rootmeta,12,tree_root,32,out_root)) return -3;
    *out_node_count = total_nodes;
    return 0;
}
