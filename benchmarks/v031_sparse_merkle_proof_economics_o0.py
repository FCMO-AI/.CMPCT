#!/usr/bin/env python3
"""O0 research only: charge candidate sparse Merkle identity, not r24 compatibility.

A sparse logical file has two DISTINCT commitments: r24 flat SHA-256 and
the experimental domain-separated leaf/tree root. Only the former is r24 law.
"""
from __future__ import annotations
import hashlib
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass

MIB = 1024 * 1024
LEAF = 64 * 1024
ZERO = bytes(LEAF)
PAD = hashlib.sha256(b'P:missing').digest()

def digest(data):
    return hashlib.sha256(data).digest()

def leaf_hash(data):
    return digest(b'L' + len(data).to_bytes(4, 'big') + data)

def node_hash(left, right):
    return digest(b'N' + left + right)

def final_root(size, leaf_size, top):
    return digest(b'F' + size.to_bytes(8, 'big') + leaf_size.to_bytes(4, 'big') + top)

@dataclass(frozen=True)
class Extent:
    offset: int
    data: bytes

def check_extents(size, extents):
    out = sorted(extents, key=lambda e: e.offset)
    end = 0
    for e in out:
        if e.offset < end or e.offset < 0 or not e.data or e.offset + len(e.data) > size:
            raise ValueError('overlapping, empty, or out-of-bounds extents')
        end = e.offset + len(e.data)
    return out

def original_flat_sha(size, extents):
    """Charge all logical zero bytes just as a conventional flat SHA must."""
    h = hashlib.sha256()
    pos = 0
    for e in check_extents(size, extents):
        gap = e.offset - pos
        while gap:
            count = min(gap, len(ZERO))
            h.update(ZERO[:count])
            gap -= count
        h.update(e.data)
        pos = e.offset + len(e.data)
    gap = size - pos
    while gap:
        count = min(gap, len(ZERO))
        h.update(ZERO[:count])
        gap -= count
    return h.hexdigest()

@dataclass
class Commitment:
    logical_size: int
    leaf_size: int
    root: bytes
    nonzero_leaf_hashes: dict
    levels: list
    touched_bytes_hashed: int
    zero_leaf_bytes_hashed: int
    serialized_index_bytes: int

def sparse_commitment(size, extents, leaf_size=LEAF):
    """Gifted source extent coordinates, but charge every decoder-visible leaf.

    The 48-byte descriptor/root plus 40 bytes per data-touched leaf is a
    *candidate* wire charge, even if existing CMPCT metadata might subsume
    some coordinates. Every touched leaf is rebuilt as full logical bytes.
    """
    if not 0 <= size < 2**64 or not 1 <= leaf_size < 2**32:
        raise ValueError('invalid file/leaf length')
    ordered = check_extents(size, extents)
    n = (size + leaf_size - 1) // leaf_size
    if not n:
        return Commitment(size, leaf_size, final_root(size, leaf_size, PAD), {}, [[PAD]], 0, 0, 48)
    touched = {}
    for e in ordered:
        p = 0
        while p < len(e.data):
            loc = e.offset + p
            i, inner = divmod(loc, leaf_size)
            part = min(leaf_size - inner, len(e.data) - p)
            if i not in touched:
                touched[i] = bytearray(min(leaf_size, size - i*leaf_size))
            touched[i][inner:inner+part] = e.data[p:p+part]
            p += part
    cache = {}
    leaves = []
    nonzero = {}
    hashed_zero_bytes = 0
    for i in range(n):
        length = min(leaf_size, size - i*leaf_size)
        if i in touched:
            lh = leaf_hash(bytes(touched[i]))
            nonzero[i] = lh
        else:
            if length not in cache:
                cache[length] = leaf_hash(bytes(length))
                hashed_zero_bytes += length
            lh = cache[length]
        leaves.append(lh)
    levels = [leaves]
    while len(levels[-1]) > 1:
        row = levels[-1]
        levels.append([node_hash(row[j], row[j+1] if j+1 < len(row) else PAD)
                       for j in range(0, len(row), 2)])
    return Commitment(size, leaf_size, final_root(size, leaf_size, levels[-1][0]),
                      nonzero, levels, sum(map(len, touched.values())),
                      hashed_zero_bytes, 48+40*len(nonzero))

def check_compact_index(c, hashes, root):
    """Cold reader recomputes root from charged digest map (no payload reads)."""
    n = (c.logical_size + c.leaf_size - 1)//c.leaf_size
    if any(not isinstance(i,int) or not 0 <= i < n or
           not isinstance(v,bytes) or len(v) != 32 for i,v in hashes.items()):
        return False
    row = []
    zero_cache = {}
    for i in range(n):
        length = min(c.leaf_size, c.logical_size-i*c.leaf_size)
        if i in hashes:
            row.append(hashes[i])
        else:
            if length not in zero_cache:
                zero_cache[length] = leaf_hash(bytes(length))
            row.append(zero_cache[length])
    if not row:
        row = [PAD]
    while len(row) > 1:
        row = [node_hash(row[j], row[j+1] if j+1 < len(row) else PAD)
               for j in range(0, len(row), 2)]
    return final_root(c.logical_size, c.leaf_size, row[0]) == root

def proof_for(c, index):
    if not 0 <= index < len(c.levels[0]):
        raise ValueError('leaf index out of bounds')
    path = []
    for row in c.levels[:-1]:
        sibling = index ^ 1
        path.append(row[sibling] if sibling < len(row) else PAD)
        index >>= 1
    return path

def validate_leaf(c, index, raw_data, proof):
    n = (c.logical_size+c.leaf_size-1)//c.leaf_size
    if not 0 <= index < n or len(proof) != len(c.levels)-1:
        return False
    if len(raw_data) != min(c.leaf_size, c.logical_size-index*c.leaf_size):
        return False
    acc = leaf_hash(raw_data)
    for sibling in proof:
        if len(sibling) != 32:
            return False
        acc = node_hash(acc,sibling) if index % 2 == 0 else node_hash(sibling,acc)
        index >>= 1
    return final_root(c.logical_size,c.leaf_size,acc) == c.root

def logical_slice(size, extents, start, length):
    assert 0 <= start <= size and 0 <= length <= size-start
    buf = bytearray(length)
    for e in extents:
        a = max(start, e.offset)
        b = min(start+length, e.offset+len(e.data))
        if a < b:
            buf[a-start:b-start] = e.data[a-e.offset:b-e.offset]
    return bytes(buf)

def case_data():
    p1 = hashlib.shake_256(b'cmpct-sparse-oracle-payload-A').digest(2*MIB)
    p2 = hashlib.shake_256(b'cmpct-sparse-oracle-payload-B').digest(2*MIB)
    dense = hashlib.shake_256(b'cmpct-sparse-oracle-dense').digest(16*MIB)
    return [
        ('clustered-128MiB',128*MIB,[Extent(4*MIB,p1),Extent(97*MIB,p2)]),
        ('shifted-128MiB',128*MIB,[Extent(4*MIB+31,p1),Extent(97*MIB+17,p2)]),
        ('all-holes-128MiB',128*MIB,[]),
        ('distributed-128MiB',128*MIB,[Extent(i*LEAF+7,bytes([(i%251)+1]))
                                      for i in range(128*MIB//LEAF)]),
        ('dense-16MiB',16*MIB,[Extent(0,dense)]),
        ('partial-tail-128MiB',128*MIB+17,[Extent(4*MIB,p1)]),
    ]

def clock(fn):
    w = time.perf_counter_ns()
    c = time.process_time_ns()
    value = fn()
    return value,(time.perf_counter_ns()-w)/1e6,(time.process_time_ns()-c)/1e6

def exercise_case(name,size,extents,repeats=5):
    first = sparse_commitment(size,extents)
    assert check_compact_index(first,first.nonzero_leaf_hashes,first.root)
    for i in [0,min(17,len(first.levels[0])-1),len(first.levels[0])-1]:
        raw = logical_slice(size,extents,i*LEAF,min(LEAF,size-i*LEAF))
        assert validate_leaf(first,i,raw,proof_for(first,i)),(name,i)
        changed = bytearray(raw)
        changed[0] ^= 1
        assert not validate_leaf(first,i,bytes(changed),proof_for(first,i))
        if len(first.levels)>1:
            bad = proof_for(first,i)
            bad[0] = bytes(32)
            assert not validate_leaf(first,i,raw,bad)
    assert not check_compact_index(first,first.nonzero_leaf_hashes,bytes(32))
    assert not check_compact_index(first,{**first.nonzero_leaf_hashes,len(first.levels[0]):bytes(32)},first.root)
    if first.nonzero_leaf_hashes:
        tamper = dict(first.nonzero_leaf_hashes)
        key = next(iter(tamper))
        tamper[key] = bytes(32)
        assert not check_compact_index(first,tamper,first.root)
        shifted = [Extent(extents[0].offset+1,extents[0].data),*extents[1:]]
        if all(e.offset+len(e.data)<=size for e in shifted):
            assert sparse_commitment(size,shifted).root != first.root
    assert sparse_commitment(size+1,extents).root != first.root
    rows = []
    for j in range(repeats):
        if j % 2:
            a,aw,ac = clock(lambda: original_flat_sha(size,extents))
            b,bw,bc = clock(lambda: sparse_commitment(size,extents))
        else:
            b,bw,bc = clock(lambda: sparse_commitment(size,extents))
            a,aw,ac = clock(lambda: original_flat_sha(size,extents))
        if j == 0:
            assert a == original_flat_sha(size,extents)
        assert b.root == first.root
        rows.append(dict(flat_wall_ms=aw,flat_cpu_ms=ac,
                         merkle_wall_ms=bw,merkle_cpu_ms=bc))
    return dict(case=name,logical_bytes=size,
                extent_bytes=sum(len(e.data) for e in extents),
                extent_count=len(extents),
                data_touched_leaves=len(first.nonzero_leaf_hashes),
                hashed_zero_leaf_bytes=first.zero_leaf_bytes_hashed,
                merkle_touched_bytes=first.touched_bytes_hashed,
                oracle_touched_buffer_bytes=first.touched_bytes_hashed,
                cold_selected_read_index_bytes=first.serialized_index_bytes,
                fully_charged_extra_index_bytes=first.serialized_index_bytes,
                flat_sha256=a,merkle_root=first.root.hex(),
                median_flat_wall_ms=statistics.median(r['flat_wall_ms'] for r in rows),
                median_merkle_wall_ms=statistics.median(r['merkle_wall_ms'] for r in rows),
                median_flat_cpu_ms=statistics.median(r['flat_cpu_ms'] for r in rows),
                median_merkle_cpu_ms=statistics.median(r['merkle_cpu_ms'] for r in rows),
                raw=rows)

def main():
    rows = [exercise_case(n,size,extents) for n,size,extents in case_data()]
    evidence = {
        'experiment':'independent-O0-sparse-Merkle-commitment-v1',
        'claim_scope':'gifted-extents independent research; NOT CMPCT archive or r24 SHA semantics',
        'source_sha256':digest(open(__file__,'rb').read()).hex(),
        'host':dict(python=sys.version,platform=sys.platform,pid=os.getpid()),
        'leaf_bytes':LEAF,'cases':rows,
        'limitations':[
            'Merkle root and flat logical SHA-256 are DIFFERENT identities: r24 cannot substitute roots.',
            'Fully charged 48-byte descriptor/root and 40 bytes per data-touched leaf.',
            'Source extent coordinates gifted by synthetic generator, not verified by authentic Builder.',
            'Root relies on an authoritative index/root; neither this nor flat SHA is origin authentication.',
            'Logical digest alone does not authenticate physical hole-allocation metadata.',
            'The O0 implementation buffers touched leaf payloads: extra memory scales with occupied leaves.',
            'Distributed 1B extents force near-full logical hashing and significant leaf-index bytes.',
            'No actual CMPCT Reader/extraction, storage, recovery, cold-open/native/portability or release measurement.'
        ]
    }
    print(json.dumps(evidence,indent=2,sort_keys=True))

if __name__ == '__main__':
    main()
