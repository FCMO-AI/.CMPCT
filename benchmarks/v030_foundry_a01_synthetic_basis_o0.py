#!/usr/bin/env python3
"""Frozen O0 oracle for A01 synthetic latent physical bases.

Research only. Discovery/search wall time is gifted; every representation byte is charged.
"""
from __future__ import annotations
import hashlib, itertools, json, random, sys, zlib
from dataclasses import dataclass

SEED = 0xA01C0DE
N = 8
SIZE = 128 * 1024
POS_RATE = 0.018
MEDOID_RATE = 0.004
CLUSTER_RATE = 0.014
TAG = 1


def uvarint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80); n >>= 7
    out.append(n)
    return bytes(out + bytes([n]))


def terminal(b: bytes) -> bytes:
    return zlib.compress(b, 9)


def mutate(src: bytes, rate: float, rng: random.Random) -> bytes:
    b = bytearray(src)
    k = max(1, int(len(b) * rate))
    for p in rng.sample(range(len(b)), k):
        v = rng.randrange(256)
        if v == b[p]: v = (v + 1) & 255
        b[p] = v
    return bytes(b)


def residual(root: bytes, target: bytes) -> bytes:
    assert len(root) == len(target)
    sparse = bytearray(b"S" + uvarint(len(target)))
    last = -1; changes = []
    for i, (a, b) in enumerate(zip(root, target)):
        if a != b: changes.append((i, b))
    sparse += uvarint(len(changes))
    for p, v in changes:
        sparse += uvarint(p - last); sparse.append(v); last = p
    raw = b"R" + uvarint(len(target)) + target
    return bytes(sparse) if len(sparse) < len(raw) else raw


def apply(root: bytes, r: bytes) -> bytes:
    i = 1
    def readv():
        nonlocal i
        n=0; s=0
        while True:
            x=r[i]; i+=1; n |= (x & 127) << s
            if x < 128: return n
            s += 7
    ln=readv()
    if r[0:1] == b"R": return bytes(r[i:i+ln])
    out=bytearray(root); cnt=readv(); last=-1
    for _ in range(cnt):
        d=readv(); p=last+d; out[p]=r[i]; i+=1; last=p
    assert len(out)==ln
    return bytes(out)


def root_payload(root: bytes) -> bytes:
    return bytes([TAG]) + uvarint(len(root)) + terminal(root)


def edge_payload(root: bytes, member: bytes, root_id: int) -> bytes:
    r = residual(root, member)
    return bytes([TAG]) + uvarint(root_id) + uvarint(len(r)) + terminal(r)


def direct_cost(ms):
    return sum(1 + len(uvarint(len(m))) + len(terminal(m)) for m in ms)


def one_root_cost(root, ms, root_id=0):
    return len(root_payload(root)) + sum(len(edge_payload(root,m,root_id)) for m in ms)


def best_real(ms):
    vals=[(one_root_cost(r,ms,i),i) for i,r in enumerate(ms)]
    return min(vals)


def best_two_real(ms):
    best=(10**30,None)
    for a,b in itertools.combinations(range(len(ms)),2):
        roots=(ms[a],ms[b]); cost=sum(len(root_payload(x)) for x in roots)
        for m in ms:
            cost += min(len(edge_payload(roots[0],m,0)),len(edge_payload(roots[1],m,1))) + 1
        best=min(best,(cost,(a,b)))
    return best


def synth_root(ms):
    # Coordinate-wise byte medoid. Search cost is explicitly gifted O0 work.
    out=bytearray(len(ms[0]))
    for p in range(len(out)):
        counts={}
        for m in ms: counts[m[p]]=counts.get(m[p],0)+1
        out[p]=min(counts, key=lambda v:(-counts[v],v))
    return bytes(out)


def families():
    rng=random.Random(SEED)
    proto=bytes(rng.randrange(256) for _ in range(SIZE))
    pos=[mutate(proto,POS_RATE,random.Random(SEED+100+i)) for i in range(N)]
    near=mutate(proto,MEDOID_RATE,random.Random(SEED+500))
    med=[near]+[mutate(proto,POS_RATE,random.Random(SEED+600+i)) for i in range(N-1)]
    p2=mutate(proto,0.20,random.Random(SEED+700))
    clu=[mutate(proto,CLUSTER_RATE,random.Random(SEED+800+i)) for i in range(N//2)] + [mutate(p2,CLUSTER_RATE,random.Random(SEED+900+i)) for i in range(N//2)]
    ind=[bytes(random.Random(SEED+1000+i).randrange(256) for _ in range(SIZE)) for i in range(N)]
    return {"ancestral_sparse_edits":pos,"biased_observed_medoid":med,"two_cluster":clu,"independent_random":ind}


def fingerprint(fs):
    h=hashlib.sha256()
    for name in sorted(fs):
        h.update(name.encode()+b"\0")
        for m in fs[name]: h.update(hashlib.sha256(m).digest())
    return h.hexdigest()


def verify(root, ms):
    return all(apply(root,residual(root,m))==m for m in ms)


def main():
    fs=families(); rows={}; invalid=False
    for name,ms in fs.items():
        sr=synth_root(ms)
        if not verify(sr,ms): invalid=True
        d=direct_cost(ms); br,bri=best_real(ms); bt,bti=best_two_real(ms); sc=one_root_cost(sr,ms,0)
        rows[name]={"direct":d,"best_real":br,"best_real_index":bri,"best_two_real":bt,"best_two_real_indices":bti,"synthetic":sc,"synthetic_vs_real_bytes":sc-br,"synthetic_vs_real_frac":(sc-br)/br,"synthetic_vs_two_real_bytes":sc-bt,"synthetic_vs_two_real_frac":(sc-bt)/bt,"roundtrip":verify(sr,ms)}
    if invalid: decision="INSTRUMENT_INVALID"
    else:
        p=rows["ancestral_sparse_edits"]; rnd=rows["independent_random"]
        material=(p["synthetic"] <= p["best_real"]-4096 and p["synthetic"] <= int(p["best_real"]*0.99))
        hostile_ok=not (rnd["synthetic"] <= int(rnd["best_real"]*0.99))
        if material and p["synthetic"] <= int(p["best_two_real"]*1.01) and hostile_ok: decision="O0_HEADROOM"
        elif material and p["best_two_real"] < int(p["synthetic"]*0.99): decision="MULTIROOT_EXPLAINS_GAIN"
        else: decision="NO_ACTIONABLE_HEADROOM"
    out={"schema":"cmpct-v030-foundry-a01-synthetic-basis-o0-v1","seed":SEED,"n":N,"size":SIZE,"rates":{"positive":POS_RATE,"medoid":MEDOID_RATE,"cluster":CLUSTER_RATE},"corpus_fingerprint":fingerprint(fs),"oracle_gifts":["root search/discovery wall time","temporary analysis memory"],"charged":["root bytes","residual bytes","descriptors","terminal bytes","exact reconstruction"],"rows":rows,"decision":decision}
    print(json.dumps(out,sort_keys=True,indent=2))
    return 2 if decision=="INSTRUMENT_INVALID" else 0

if __name__=="__main__": sys.exit(main())
