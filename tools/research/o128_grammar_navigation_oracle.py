#!/usr/bin/env python3
"""O128 A07: charged, exact binary-grammar navigation oracle; NOT an r24 archive.

Use the SAME terminal payload dictionary for grammar, flat and grouped controls.
Gift grammar discovery/search work but do not award product cost or release credit.
"""
import ctypes
import ctypes.util
import hashlib
import json
import random
import resource
import statistics
import sys
import time
from collections import Counter

SEEDS=(31,101,2026,4096)
FAMILIES=('motifs','rotations','independent_refs','opaque')
N_FILES=16
BPF=64
BLOCK_SIZE=256
MAX_RULES=96
lib=ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so.1')
lib.ZSTD_compressBound.argtypes=[ctypes.c_size_t]
lib.ZSTD_compressBound.restype=ctypes.c_size_t
lib.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
lib.ZSTD_compress.restype=ctypes.c_size_t
lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
lib.ZSTD_decompress.restype=ctypes.c_size_t
lib.ZSTD_isError.argtypes=[ctypes.c_size_t]
lib.ZSTD_isError.restype=ctypes.c_uint
lib.ZSTD_getErrorName.argtypes=[ctypes.c_size_t]
lib.ZSTD_getErrorName.restype=ctypes.c_char_p

def z19(data):
    dst=ctypes.create_string_buffer(lib.ZSTD_compressBound(len(data)))
    size=lib.ZSTD_compress(dst,len(dst),ctypes.c_char_p(data),len(data),19)
    if lib.ZSTD_isError(size): raise RuntimeError(lib.ZSTD_getErrorName(size).decode())
    return dst.raw[:size]

def zd(data,size):
    dst=ctypes.create_string_buffer(max(1,size))
    actual=lib.ZSTD_decompress(dst,len(dst),ctypes.c_char_p(data),len(data))
    if lib.ZSTD_isError(actual): raise RuntimeError(lib.ZSTD_getErrorName(actual).decode())
    assert actual==size
    return dst.raw[:actual]

def v(number):
    assert 0<=number<(1<<40)
    result=bytearray()
    while number>=128:
        result.append(128|(number&127))
        number>>=7
    result.append(number)
    return bytes(result)

def encoded(seq):
    raw=b''.join(v(i) for i in seq)
    packed=z19(raw)
    assert zd(packed,len(raw))==raw
    return raw if len(raw)<=len(packed) else packed

def data(seed,family):
    r=random.Random(seed*773+sum(map(ord,family)))
    pool=[r.randbytes(BLOCK_SIZE) for _ in range(80)]
    common=[r.randrange(80) for _ in range(BPF)]
    motifs=[[r.randrange(80) for _ in range(8)] for _ in range(4)]
    result=[]
    for f in range(N_FILES):
        if family=='motifs':
            ids=[x for j in range(8) for x in motifs[(j+f%2)%4]]
            for j in range(f%7): ids[(j*11+f*3)%BPF]=r.randrange(80)
            pieces=[pool[i] for i in ids]
        elif family=='rotations':
            shift=f*7%64
            ids=common[shift:]+common[:shift]
            for j in range(f%5+1): ids[(j*13+f)%BPF]=r.randrange(80)
            pieces=[pool[i] for i in ids]
        elif family=='independent_refs':
            pieces=[pool[r.randrange(80)] for _ in range(BPF)]
        elif family=='opaque':
            pieces=[r.randbytes(BLOCK_SIZE) for _ in range(BPF)]
        else: raise ValueError(family)
        result.append(b''.join(pieces))
    return result

def dedup(members):
    blocks=[]; ids={}; chains=[]
    for member in members:
        row=[]
        for j in range(0,len(member),BLOCK_SIZE):
            part=member[j:j+BLOCK_SIZE]
            if part not in ids:
                ids[part]=len(blocks)
                blocks.append(part)
            row.append(ids[part])
        chains.append(tuple(row))
    assert all(b''.join(blocks[k] for k in row)==src for row,src in zip(chains,members))
    return blocks,chains

def versions_of(chains,nterms):
    heads=[tuple(row) for row in chains]; rules=[]
    yield list(heads),list(rules)
    for _ in range(MAX_RULES):
        ct=Counter()
        for row in heads: ct.update(zip(row,row[1:]))
        if not ct: break
        pair,freq=min(ct.items(),key=lambda kv:(-kv[1],kv[0]))
        if freq<3: break
        new_id=nterms+len(rules)
        newer=[]
        for row in heads:
            out=[]; j=0
            while j<len(row):
                if j+1<len(row) and (row[j],row[j+1])==pair:
                    out.append(new_id); j+=2
                else:
                    out.append(row[j]); j+=1
            newer.append(tuple(out))
        if sum(map(len,newer))>=sum(map(len,heads)): break
        rules.append(pair);heads=newer
        yield list(heads),list(rules)

def grammar_cost(roots,rules,nterms):
    spans=[1]*nterms
    for a,b in rules: spans.append(spans[a]+spans[b])
    table=b''.join(v(a)+v(b)+v(spans[nterms+j]) for j,(a,b) in enumerate(rules))
    packed=z19(table)
    assert zd(packed,len(table))==table
    # Shared directory + codec + rule count + raw-or-zstd table; no free length.
    table_bytes=8+1+len(v(len(rules)))+min(len(table),len(packed))
    controls=sum(8+1+len(v(len(row)))+len(encoded(row)) for row in roots)
    return table_bytes+controls,spans,table

def flat_cost(chains):
    return sum(8+1+len(v(len(row)))+len(encoded(row)) for row in chains)

def grouped(chains,group_size):
    total=0;worst_uncompressed=0
    for i in range(0,len(chains),group_size):
        rows=chains[i:i+group_size]
        raw=b''.join(v(len(row))+b''.join(v(k) for k in row) for row in rows)
        compressed=z19(raw)
        assert zd(compressed,len(raw))==raw
        # Frame locator, encoded+decoded lengths, codec, group count, bytes.
        total+=8+4+4+1+len(v(len(rows)))+min(len(raw),len(compressed))
        worst_uncompressed=max(worst_uncompressed,len(raw))
    return total,worst_uncompressed

def expand(symbol,rules,nterms):
    if symbol<nterms: return [symbol]
    a,b=rules[symbol-nterms]
    return expand(a,rules,nterms)+expand(b,rules,nterms)

def select(root,rules,spans,nterms,logical_block):
    visited=0
    def descend(node,at):
        nonlocal visited
        visited+=1
        if node<nterms:
            assert at==0
            return node
        a,b=rules[node-nterms]
        return descend(a,at) if at<spans[a] else descend(b,at-spans[a])
    j=logical_block
    for node in root:
        if j>=spans[node]: j-=spans[node]
        else: return descend(node,j),visited
    raise AssertionError('out of range')

def one(seed,family):
    start=time.perf_counter()
    members=data(seed,family)
    blocks,chains=dedup(members); nterms=len(blocks)
    # Same actual Zstd-19 physical blocks for all three navigation layouts.
    # Charge every terminal frame, SHA256 identity, extent and locator.
    common=64+sum(4+32+4+len(z19(b)) for b in blocks)
    common+=sum(8+len(f'member{i:03d}'.encode())+32 for i in range(N_FILES))
    flat_total=common+flat_cost(chains)+1
    best=None
    for roots,rules in versions_of(chains,nterms):
        cost,spans,table=grammar_cost(roots,rules,nterms)
        total=common+cost+1
        if best is None or (total,len(rules))<(best[0],len(best[2])):
            best=(total,roots,rules,spans,table)
    total,roots,rules,spans,table=best
    decode_amp=0.; visited=[]
    for index,(root,src) in enumerate(zip(roots,members)):
        decoded=[]
        for sym in root: decoded+=expand(sym,rules,nterms)
        assert decoded==list(chains[index])
        assert hashlib.sha256(b''.join(blocks[k] for k in decoded)).digest()==hashlib.sha256(src).digest()
        for j in (0,17,31,63):
            terminal,steps=select(root,rules,spans,nterms,j)
            assert blocks[terminal]==src[j*BLOCK_SIZE:(j+1)*BLOCK_SIZE]
            cold_control=len(table)+len(v(len(root)))+sum(len(v(k)) for k in root)
            decode_amp=max(decode_amp,(BLOCK_SIZE+cold_control)/BLOCK_SIZE)
            visited.append(steps)
    group_controls=[]
    for group_size in (1,2,4,8,16):
        cost,decoded=grouped(chains,group_size)
        group_controls.append({
            'group':group_size,'complete_bytes':common+cost+1,
            'selective_decode_amplification':round((BLOCK_SIZE+decoded)/BLOCK_SIZE,3)
        })
    eligible=[g for g in group_controls if g['selective_decode_amplification']<=8]
    strong=min(eligible,key=lambda g:(g['complete_bytes'],g['group']))
    direct=64+sum(8+len(f'member{i:03d}')+32+len(z19(src)) for i,src in enumerate(members))
    solid_content=b''.join(v(len(src))+f'member{i:03d}'.encode()+src for i,src in enumerate(members))
    solid=64+len(z19(solid_content))+N_FILES*(8+32)
    return {
        'seed':seed,'family':family,'members':N_FILES,'input_bytes':sum(map(len,members)),
        'unique_blocks':nterms,'dictionary_and_common_bytes':common,
        'flat_selective_bytes':flat_total,'grammar_selective_bytes':total,'grammar_rules':len(rules),
        'grammar_win_vs_flat_bytes':flat_total-total,
        'grammar_win_vs_flat_pct':round(100*(flat_total-total)/flat_total,4),
        'grouped_baselines':group_controls,
        'best_grouped_selective_bytes':strong['complete_bytes'],
        'best_grouped_selective_group':strong['group'],
        'grammar_gain_vs_best_grouped_bytes':strong['complete_bytes']-total,
        'grammar_gain_vs_best_grouped_pct':round(100*(strong['complete_bytes']-total)/strong['complete_bytes'],4),
        'per_member_z19_size_only_bytes':direct,'solid_z19_size_only_bytes':solid,
        'max_grammar_cold_decode_amplification':round(decode_amp,3),
        'median_grammar_seek_nodes':statistics.median(visited),
        'input_sha256':hashlib.sha256(b''.join(members)).hexdigest(),
        'oracle_elapsed_s':round(time.perf_counter()-start,3)
    }

def main():
    start=time.perf_counter()
    results=[one(seed,family) for family in FAMILIES for seed in SEEDS]
    qualified=sorted({r['family'] for r in results if r['grammar_gain_vs_best_grouped_pct']>=1 and r['max_grammar_cold_decode_amplification']<=8})
    decision='FURTHER_EVALUATION_CANDIDATE' if len(qualified)>=2 else 'REJECT_BINARY_GRAMMAR_AS_BYTE_WINNER'
    payload={'schema':'cmpct-o128-a07-grammar-navigation-r0','source':'reproducible lower-rung oracle, not r24 product',
        'input_contract':'16 members x 64 exact 256B blocks; four deterministic seeds; generic content-only IDs',
        'codec':'libzstd ZSTD_compress level 19 frames','results':results,
        'qualified_families':qualified,'byte_headroom_decision':decision,
        'oracle_elapsed_s':round(time.perf_counter()-start,3),
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'product_credit':False,'official_benchmark':False}
    assert all(r['max_grammar_cold_decode_amplification']<=8 for r in results)
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': sys.exit(main())
