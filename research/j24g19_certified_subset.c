/* J24G19 RESEARCH ONLY. Positive means a conservative proof that unpackb(raw=False)
 * will accept this complete subset's syntax and strictly string-keyed map shape.
 * Unsupported or dubious syntax is a *miss*, never an acceptance or rejection.
 * No allocations and no change to CMPCT's metadata or format.
 */
#include <stddef.h>
#include <stdint.h>

struct cursor { const unsigned char *p, *e; uint64_t nodes; };
static int take(struct cursor *c, size_t n) {
    if ((size_t)(c->e - c->p) < n) return 0;
    c->p += n; return 1;
}
static int number(struct cursor *c, unsigned bytes, uint32_t *out) {
    if ((size_t)(c->e-c->p)<bytes) return 0;
    uint32_t n=0;
    for (unsigned i=0; i<bytes; ++i) n=(n<<8)|*c->p++;
    *out=n; return 1;
}
static int ascii_string(struct cursor *c, unsigned n) {
    if ((size_t)(c->e-c->p)<n) return 0;
    for (unsigned i=0; i<n; ++i) if (c->p[i]&0x80) return 0;
    c->p+=n;return 1;
}
static int walk(struct cursor *c, unsigned depth, int map_key) {
    if (depth>=32 || c->p>=c->e) return 0;
    ++c->nodes;
    unsigned code=*c->p++;
    if (map_key) {
        /* Restrict keys to small ASCII strings. strict_map_key=True accepts these,
         * and no Unicode/ExtType/equality/hash corner-case is possible here. */
        if (code<0xa0 || code>0xbf) return 0;
        return ascii_string(c, code&31);
    }
    if (code<=0x7f || code>=0xe0 || code==0xc0 || code==0xc2 || code==0xc3) return 1;
    if (code>=0xa0 && code<=0xbf) return ascii_string(c,code&31);
    if (code==0xcc || code==0xd0) return take(c,1);
    if (code==0xcd || code==0xd1) return take(c,2);
    if (code==0xce || code==0xd2) return take(c,4);
    if (code==0xcf || code==0xd3) return take(c,8);
    uint32_t n=0; int is_map=0;
    if (code>=0x80 && code<=0x8f) {n=code&15;is_map=1;}
    else if (code>=0x90 && code<=0x9f) n=code&15;
    else if (code==0xdc || code==0xde) {
        if (!number(c,2,&n)) return 0;
        is_map=code==0xde;
    } else if (code==0xdd || code==0xdf) {
        if (!number(c,4,&n)) return 0;
        is_map=code==0xdf;
    } else return 0;
    /* A valid item occupies at least 1 byte, a map pair at least 2. Short
     * vectors are therefore rejected before entering potentially huge loops. */
    if ((uint64_t)n > (uint64_t)(c->e-c->p)/(is_map?2u:1u)) return 0;
    for(uint32_t i=0;i<n;++i) {
        if (is_map && !walk(c,depth+1,1)) return 0;
        if (!walk(c,depth+1,0)) return 0;
    }
    return 1;
}
int mp_certify_subset(const unsigned char *p, size_t n, uint64_t *out_nodes) {
    if (!p || !out_nodes || !n || n>(16u<<20)) return 0;
    struct cursor c={p,p+n,0};
    if (!walk(&c,0,0) || c.p!=c.e) return 0;
    *out_nodes=c.nodes;return 1;
}
