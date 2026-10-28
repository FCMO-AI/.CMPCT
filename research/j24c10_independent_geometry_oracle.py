#!/usr/bin/env python3
"""Independent bounded algebraic uniform-stride range oracle (no CMPCT import).

Tests constant-stride + optional shorter tail against literal concatenation
for every interval on all positive owner-length vectors n=1..8 over {1,2,4}.
A negative means no arithmetic shortcut; the inherited scanner remains required.
"""
from itertools import product


def run():
    checked=0
    accepted=0
    for n in range(1,9):
        for lengths in product((1,2,4),repeat=n):
            blobs=[bytes([i+1])*ln for i,ln in enumerate(lengths)]
            raw=b"".join(blobs)
            stride=(lengths[0] if all(x==lengths[0] for x in lengths[:-1])
                    and lengths[-1]<=lengths[0] else 0)
            if not stride:
                continue
            accepted+=1
            for start in range(len(raw)+1):
                for end in range(start,len(raw)+1):
                    first=start//stride
                    p=first*stride
                    parts=[]
                    for j in range(first,n):
                        block=blobs[j]
                        length=len(block)
                        if p+length>start and p<end:
                            lo=max(start,p)-p
                            hi=min(end,p+length)-p
                            parts.append(block[lo:hi])
                        p+=length
                        if p>=end:
                            break
                    got=b"".join(parts)
                    assert got==raw[start:end],(lengths,start,end,got,raw[start:end])
                    checked+=1
    assert accepted>0 and checked>=5000
    print("J24C10_INDEPENDENT_EXHAUSTIVE_GEOMETRY_PASS",accepted,"vectors",checked,"ranges")


if __name__=="__main__":
    run()
