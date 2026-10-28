/* J24G17 RESEARCH ONLY -- bounded syntactic MessagePack token scan.
 * This function NEVER authorizes decoding/acceptance: normal msgpack.unpackb
 * is still the semantic authority for payloads under the test-only token cap.
 * Return 1 accepted syntactic structure under cap; 0 exceeds budget;
 * -1 malformed wire framing. No CPython allocation inside this scanner.
 * No on-disk format or released CMPCT code changes.
 */
#include <stddef.h>
#include <stdint.h>

static int take(const unsigned char **q, const unsigned char *e, size_t k) {
    if ((size_t)(e-*q) < k) return 0;
    *q += k; return 1;
}
static int readn(const unsigned char **q, const unsigned char *e, unsigned n, uint32_t *out) {
    if ((size_t)(e-*q)<n) return 0;
    uint32_t x=0;
    for (unsigned i=0; i<n; ++i) x=(x<<8)|*((*q)++);
    *out=x; return 1;
}
/* one object traversal with an unbounded logical pending count, bounded by
 * max_nodes itself. Depth is not accepted as a semantic claim; canonical
 * decoder still validates full nesting. An overflowing container is refused.
 */
int mp_count_tokens(const unsigned char *ptr,size_t len,uint64_t max_nodes,uint64_t *out_nodes) {
    if (!ptr || !out_nodes || max_nodes==0 || len==0) return -1;
    const unsigned char *p=ptr,*e=ptr+len;
    uint64_t pending=1, nodes=0;
    while (pending) {
        if (p==e) return -1;
        if (++nodes>max_nodes) { *out_nodes=nodes; return 0; }
        --pending;
        unsigned c=*p++;
        uint32_t n=0; uint64_t children=0;
        if (c<=0x7f || c>=0xe0 || c==0xc0 || c==0xc2 || c==0xc3) {}
        else if (c>=0x80 && c<=0x8f) children=(uint64_t)(c&15)*2;
        else if (c>=0x90 && c<=0x9f) children=c&15;
        else if (c>=0xa0 && c<=0xbf) {if(!take(&p,e,c&31))return -1;}
        else if (c==0xc1) return -1;
        else if (c==0xc4 || c==0xd9) {if(!readn(&p,e,1,&n)||!take(&p,e,n))return -1;}
        else if (c==0xc5 || c==0xda) {if(!readn(&p,e,2,&n)||!take(&p,e,n))return -1;}
        else if (c==0xc6 || c==0xdb) {if(!readn(&p,e,4,&n)||!take(&p,e,n))return -1;}
        else if (c==0xc7 || c==0xc8 || c==0xc9) {
            if(!readn(&p,e,c==0xc7?1:c==0xc8?2:4,&n))return -1;
            if((size_t)(e-p)<1 || !take(&p,e,1) || !take(&p,e,n))return -1;
        }
        else if (c==0xca || c==0xce || c==0xd2) {if(!take(&p,e,4))return -1;}
        else if (c==0xcb || c==0xcf || c==0xd3) {if(!take(&p,e,8))return -1;}
        else if (c==0xcc || c==0xd0) {if(!take(&p,e,1))return -1;}
        else if (c==0xcd || c==0xd1) {if(!take(&p,e,2))return -1;}
        else if (c>=0xd4 && c<=0xd8) {if(!take(&p,e,(1u<<(c-0xd4))+1))return -1;}
        else if (c==0xdc || c==0xde) {
            if(!readn(&p,e,2,&n))return -1;
            children=c==0xde?(uint64_t)n*2:n;
        }
        else if (c==0xdd || c==0xdf) {
            if(!readn(&p,e,4,&n))return -1;
            children=c==0xdf?(uint64_t)n*2:n;
        }
        else return -1;
        if (children>max_nodes-nodes || pending>max_nodes-nodes-children) {
            *out_nodes=nodes; return 0;
        }
        pending+=children;
    }
    if(p!=e)return -1;
    *out_nodes=nodes;
    return 1;
}
