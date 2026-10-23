#!/usr/bin/env python3
"""O1 research only: sparse-Merkle cold root/proof without O(logical-leaves) memory.

Root semantics exactly match O0 (PR #276); the conventional r24 SHA-256 does NOT.
Source extent offsets are gifted, and there is no CMPCT product format/reader.
"""
from __future__ import annotations
import bisect
import hashlib
import json
import random
import struct
import sys
import time
import tracemalloc

from v031_sparse_merkle_proof_economics_o0 import (
    Extent, PAD, check_extents, leaf_hash, node_hash, final_root,
)
from v031_sparse_merkle_independent_falsifier import reference_root

HEAD = struct.Struct('>4sQI32s')  # 48 bytes: marker, logical length, leaf bytes, root
ROW = struct.Struct('>Q32s')    # 40 bytes: leaf ordinal and its digest


class Collapsed:
    def __init__(self, size, leaf, digests):
        if type(size) is not int or type(leaf) is not int or not (0 <= size < 2**64) or not (1 <= leaf < 2**32):
            raise ValueError('bad length or leaf size')
        self.size, self.leaf = size, leaf
        self.n = (size + leaf - 1) // leaf
        self.height = (self.n - 1).bit_length() if self.n else 0
        self.data = dict(digests)
        for i, digest in self.data.items():
            if type(i) is not int or not 0 <= i < self.n or type(digest) is not bytes or len(digest) != 32:
                raise ValueError('invalid charged digest row')
        self.keys = sorted(self.data)
        self.zero = {0: leaf_hash(bytes(leaf))}
        self.cache = {}
        self.visited = 0

    def empty(self, height):
        for h in range(1, height + 1):
            if h not in self.zero:
                d = self.zero[h - 1]
                self.zero[h] = node_hash(d, d)
        return self.zero[height]

    def subtree(self, start, height):
        if start >= self.n:
            return PAD   # O0 odd-row siblings are PAD, not hashed PAD subtrees
        key = (start, height)
        if key in self.cache:
            return self.cache[key]
        self.visited += 1
        end = start + (1 << height)
        p = bisect.bisect_left(self.keys, start)
        occupied = p < len(self.keys) and self.keys[p] < end
        if not occupied and (end < self.n or (end == self.n and self.size % self.leaf == 0)):
            d = self.empty(height)
        elif height == 0:
            count = min(self.leaf, self.size - start * self.leaf)
            d = self.data[start] if start in self.data else leaf_hash(bytes(count))
        else:
            half = 1 << (height - 1)
            d = node_hash(self.subtree(start, height - 1),
                          self.subtree(start + half, height - 1))
        self.cache[key] = d
        return d

    @property
    def root(self):
        return final_root(self.size, self.leaf, self.subtree(0, self.height) if self.n else PAD)

    def siblings(self, index):
        if type(index) is not int or not 0 <= index < self.n:
            raise ValueError('bad proof position')
        start, path = 0, []
        for h in range(self.height, 0, -1):
            half = 1 << (h - 1)
            if index < start + half:
                path.append(self.subtree(start + half, h - 1))
            else:
                path.append(self.subtree(start, h - 1))
                start += half
        return list(reversed(path))

    def verify_leaf(self, index, raw, siblings, trusted_root):
        if type(index) is not int or not 0 <= index < self.n or len(siblings) != self.height:
            return False
        if len(raw) != min(self.leaf, self.size - index * self.leaf):
            return False
        value = leaf_hash(raw)
        for neighbor in siblings:
            if type(neighbor) is not bytes or len(neighbor) != 32:
                return False
            value = node_hash(value, neighbor) if index % 2 == 0 else node_hash(neighbor, value)
            index >>= 1
        return final_root(self.size, self.leaf, value) == trusted_root

    def serialize(self):
        return HEAD.pack(b'SMO1', self.size, self.leaf, self.root) + b''.join(
            ROW.pack(i, self.data[i]) for i in self.keys)

    @classmethod
    def reopen(cls, raw, max_rows=100_000):
        if len(raw) < HEAD.size or (len(raw) - HEAD.size) % ROW.size:
            raise ValueError('truncated / unaligned index')
        marker, size, leaf, expected = HEAD.unpack_from(raw)
        if marker != b'SMO1' or (len(raw) - HEAD.size) // ROW.size > max_rows:
            raise ValueError('invalid version or resource budget')
        records, previous = [], -1
        for pos in range(HEAD.size, len(raw), ROW.size):
            i, d = ROW.unpack_from(raw, pos)
            if i <= previous:
                raise ValueError('duplicate or unordered index')
            previous = i
            records.append((i, d))
        obj = cls(size, leaf, records)
        if obj.root != expected:
            raise ValueError('root mismatch')
        return obj


def from_extents(size, leaf, extents):
    """Gifted positions; builds only occupied logical leaves, not every zero leaf."""
    touched = {}
    for e in check_extents(size, extents):
        at = 0
        while at < len(e.data):
            i, inner = divmod(e.offset + at, leaf)
            count = min(leaf - inner, len(e.data) - at)
            if i not in touched:
                touched[i] = bytearray(min(leaf, size - i * leaf))
            touched[i][inner:inner + count] = e.data[at:at + count]
            at += count
    return Collapsed(size, leaf, {i: leaf_hash(bytes(d)) for i, d in touched.items()})


def disprove_bad_wire(wire):
    bad = [
        wire + wire[-40:],                     # duplicate and unsorted
        wire[:16] + bytes(32) + wire[48:],     # forgery of root
        wire[:48] + wire[-40:] + wire[48:-40], # reordered rows
        wire[:-1],                             # truncation
    ]
    for candidate in bad:
        try:
            Collapsed.reopen(candidate)
        except ValueError:
            continue
        raise AssertionError('adversarial descriptor accepted')


def main():
    rng = random.Random(20261023)
    checks = 0
    for trial in range(320):
        size = [0, 1, 4095, 4096, 4097, 8192, 8193, 200001][trial % 8] if trial < 64 else rng.randrange(0, 220000)
        full = bytearray(size)
        extents, seen = [], bytearray(size)
        for _ in range(rng.randrange(0, 7)):
            if not size:
                break
            p = rng.randrange(size)
            count = min(size - p, rng.randrange(1, 3000))
            if any(seen[p:p + count]):
                continue
            payload = rng.randbytes(count)
            full[p:p + count] = payload
            seen[p:p + count] = bytes([1]) * count
            extents.append(Extent(p, payload))
        for leaf in (4096, 65536):
            compact = from_extents(size, leaf, extents)
            independently_computed = reference_root(full, leaf)
            assert compact.root == independently_computed, (trial, leaf)
            wire = compact.serialize()
            reopened = Collapsed.reopen(wire)
            assert reopened.root == independently_computed
            for i in ({0, compact.n // 2, compact.n - 1} if compact.n else set()):
                raw = bytes(full[i * leaf:(i + 1) * leaf])
                proof = reopened.siblings(i)
                assert reopened.verify_leaf(i, raw, proof, compact.root)
                forged = bytearray(raw)
                forged[0] ^= 1
                assert not reopened.verify_leaf(i, forged, proof, compact.root)
                if proof:
                    bad = list(proof)
                    bad[0] = bytes(32)
                    assert not reopened.verify_leaf(i, raw, bad, compact.root)
            checks += 1

    # Memory falsifier: O0 would create >16 million full leaf nodes for 1 TiB.
    size, leaf = 1 << 40, 65536
    e = [Extent(7 * (1 << 30) + 3, b'abc'), Extent(size - 2, b'XY')]
    tracemalloc.start()
    start = time.perf_counter()
    tree = from_extents(size, leaf, e)
    wire = tree.serialize()
    cold = Collapsed.reopen(wire)
    t = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert tree.root == cold.root
    assert len(wire) == 48 + 40 * 2 and peak < 5 * (1 << 20)
    assert tree.visited < 300 and cold.visited < 300 and t < 2
    last = cold.n - 1
    raw = bytes(leaf - 2) + b'XY'
    assert cold.verify_leaf(last, raw, cold.siblings(last), tree.root)
    assert not cold.verify_leaf(last, bytes(leaf), cold.siblings(last), tree.root)
    assert cold.verify_leaf(0, bytes(leaf), cold.siblings(0), tree.root)
    disprove_bad_wire(wire)

    # Explicit negative: high occupancy cannot avoid charging its hash/index rows.
    dense_charge = 48 + 40 * (size // leaf)
    assert dense_charge > (1 << 28)
    print(json.dumps({
        'evidence_tier':'O1 research; NOT revision-24 SHA identity or CMPCT product',
        'reference_differentials': checks,
        'logical_1tib_bytes': size, 'descriptor_bytes': len(wire),
        'cold_root_matches': True, 'root_hex': tree.root.hex(),
        'cold_visited_nodes': cold.visited, 'creator_visited_nodes': tree.visited,
        'tracemalloc_peak_bytes': peak, 'one_tib_wall_s': t,
        'hypothetical_dense_index_bytes':dense_charge,
        'status':'PASS','python':sys.version.split()[0]
    }, sort_keys=True))


if __name__ == '__main__':
    main()
