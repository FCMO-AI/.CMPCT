#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
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
static int hash_leaf(uint64_t index,uint64_t total,const uint8_t *payload,size_t n,uint8_t out[32]) {
    uint8_t meta[16]; le64(meta,index); le64(meta+8,total);
    SHA256_CTX ctx;
    if (!SHA256_Init(&ctx) || !SHA256_Update(&ctx,LEAF_DOMAIN,6) || !SHA256_Update(&ctx,meta,16)) return 0;
    if (n && !SHA256_Update(&ctx,payload,n)) return 0;
    return SHA256_Final(out,&ctx)==1;
}
static int hash_parent(uint32_t level,const uint8_t left[32],const uint8_t right[32],uint8_t out[32]) {
    uint8_t meta[4]; le32(meta,level);
    SHA256_CTX ctx;
    return SHA256_Init(&ctx) && SHA256_Update(&ctx,PARENT_DOMAIN,6) && SHA256_Update(&ctx,meta,4) &&
           SHA256_Update(&ctx,left,32) && SHA256_Update(&ctx,right,32) && SHA256_Final(out,&ctx);
}
static int root_commit(uint64_t total,uint32_t leaf_bytes,const uint8_t tree_root[32],uint8_t out[32]) {
    uint8_t meta[12]; le64(meta,total); le32(meta+8,leaf_bytes);
    SHA256_CTX ctx;
    return SHA256_Init(&ctx) && SHA256_Update(&ctx,ROOT_DOMAIN,6) && SHA256_Update(&ctx,meta,12) &&
           SHA256_Update(&ctx,tree_root,32) && SHA256_Final(out,&ctx);
}

/*
 * Verify the exact experiments.one.auth_tree RangeProof grammar for a contiguous leaf interval.
 * siblings_* are the existing proof triples split into level/index/digest arrays, in proof order.
 * Returns 0 success, -1 invalid request/arguments, -2 malformed proof geometry, -3 SHA failure,
 * -4 root mismatch, -5 output capacity/coverage failure, -6 allocation failure.
 */
int one_auth_verify_interval_native(
    uint64_t total_len, uint32_t leaf_bytes, uint64_t first_leaf,
    const uint8_t *payload_bytes, size_t payload_bytes_len, size_t payload_count,
    const uint32_t *sibling_levels, const uint64_t *sibling_indices,
    const uint8_t *sibling_hashes, size_t sibling_count,
    const uint8_t expected_root[32], uint64_t start, uint64_t length,
    uint8_t *out, size_t out_capacity
) {
    if (!leaf_bytes || !expected_root || (payload_bytes_len && !payload_bytes) ||
        (sibling_count && (!sibling_levels || !sibling_indices || !sibling_hashes)) ||
        (length && !out)) return -1;
    if (start > total_len || length > total_len-start || out_capacity < length) return -1;
    uint64_t leaf_count = total_len ? (total_len + leaf_bytes - 1u) / leaf_bytes : 1u;
    if (!payload_count || first_leaf >= leaf_count || payload_count > leaf_count-first_leaf) return -2;
    uint64_t last_leaf = first_leaf + payload_count - 1u;
    if (length) {
        uint64_t expect_first = start / leaf_bytes;
        uint64_t expect_last = (start + length - 1u) / leaf_bytes;
        if (expect_first != first_leaf || expect_last != last_leaf) return -2;
    } else {
        uint64_t expect_first = start / leaf_bytes;
        if (expect_first >= leaf_count) expect_first = leaf_count-1u;
        if (first_leaf != expect_first || payload_count != 1u) return -2;
    }

    size_t max_nodes = payload_count + 2u;
    if (max_nodes > SIZE_MAX/32u) return -2;
    uint8_t *cur = (uint8_t*)malloc(max_nodes*32u);
    uint8_t *next = (uint8_t*)malloc(max_nodes*32u);
    if (!cur || !next) { free(cur); free(next); return -6; }

    size_t payload_off=0;
    for (size_t j=0;j<payload_count;j++) {
        uint64_t idx=first_leaf+j;
        uint64_t begin=idx*(uint64_t)leaf_bytes;
        size_t n=0;
        if (begin < total_len) {
            uint64_t remain=total_len-begin;
            n=(size_t)(remain < leaf_bytes ? remain : leaf_bytes);
        }
        if (n > payload_bytes_len-payload_off) { free(cur); free(next); return -2; }
        if (!hash_leaf(idx,total_len,payload_bytes+payload_off,n,cur+j*32u)) { free(cur); free(next); return -3; }
        payload_off += n;
    }
    if (payload_off != payload_bytes_len) { free(cur); free(next); return -2; }

    uint64_t lo=first_leaf, hi=last_leaf, width=leaf_count;
    size_t cur_count=payload_count, sib_pos=0;
    uint32_t level=0;
    while (width > 1u) {
        int need_left=(lo & 1u) != 0;
        uint64_t right_idx=hi+1u;
        int need_right=((hi & 1u)==0) && right_idx < width;
        const uint8_t *left_sib=NULL, *right_sib=NULL;
        if (need_left) {
            if (sib_pos>=sibling_count || sibling_levels[sib_pos]!=level || sibling_indices[sib_pos]!=lo-1u) { free(cur); free(next); return -2; }
            left_sib=sibling_hashes+sib_pos*32u; sib_pos++;
        }
        if (need_right) {
            if (sib_pos>=sibling_count || sibling_levels[sib_pos]!=level || sibling_indices[sib_pos]!=right_idx) { free(cur); free(next); return -2; }
            right_sib=sibling_hashes+sib_pos*32u; sib_pos++;
        }

        uint64_t parent_lo=lo/2u, parent_hi=hi/2u;
        size_t next_count=(size_t)(parent_hi-parent_lo+1u);
        for (size_t k=0;k<next_count;k++) {
            uint64_t p=parent_lo+k, li=2u*p, ri=li+1u;
            const uint8_t *left=NULL,*right=NULL;
            if (li < lo) left=left_sib;
            else if (li <= hi) left=cur+(size_t)(li-lo)*32u;
            if (ri < lo) right=left_sib;
            else if (ri <= hi) right=cur+(size_t)(ri-lo)*32u;
            else if (ri < width) right=right_sib;
            else right=left;
            if (!left || !right || !hash_parent(level+1u,left,right,next+k*32u)) { free(cur); free(next); return left&&right ? -3 : -2; }
        }
        uint8_t *tmp=cur; cur=next; next=tmp;
        cur_count=next_count;
        lo=parent_lo; hi=parent_hi; width=(width+1u)/2u; level++;
    }
    if (cur_count != 1u || sib_pos != sibling_count) { free(cur); free(next); return -2; }
    uint8_t committed[32];
    if (!root_commit(total_len,leaf_bytes,cur,committed)) { free(cur); free(next); return -3; }
    if (memcmp(committed,expected_root,32)!=0) { free(cur); free(next); return -4; }

    if (length) {
        uint64_t origin=first_leaf*(uint64_t)leaf_bytes;
        uint64_t rel=start-origin;
        if (rel > payload_bytes_len || length > payload_bytes_len-rel) { free(cur); free(next); return -5; }
        memcpy(out,payload_bytes+(size_t)rel,(size_t)length);
    }
    free(cur); free(next); return 0;
}
