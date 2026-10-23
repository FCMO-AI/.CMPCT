#!/usr/bin/env python3
"""Posthoc independent dyadic-stream root replication for O1 collapsed proof.

Power-of-two leaf-count only: uses sorted dyadic runs + iterative stack folding,
NOT the candidate's recursive subtree/root traversal. Research only.
"""
import hashlib
import json
import random

from v031_sparse_merkle_collapsed_o1 import Collapsed

H = lambda b: hashlib.sha256(b).digest()


def node(left, right):
    return H(b'N' + left + right)


def leaf_digest(raw):
    return H(b'L' + len(raw).to_bytes(4, 'big') + raw)


def empty_subtree(leaf_size, h, cache):
    for j in range(h + 1):
        if j not in cache:
            cache[j] = leaf_digest(bytes(leaf_size)) if j == 0 else node(cache[j-1],cache[j-1])
    return cache[h]


def independent_dyadic(size, leaf_size, occupied):
    assert size % leaf_size == 0
    n = size // leaf_size
    assert n > 0 and n & (n - 1) == 0
    cache = {}
    stack = []
    pushes = 0

    def push(start, h, digest):
        nonlocal pushes
        pushes += 1
        stack.append((start, h, digest))
        while len(stack) > 1:
            l, r = stack[-2:]
            if l[1] != r[1] or l[0] + (1 << l[1]) != r[0] or l[0] % (2 << l[1]):
                break
            stack[-2:] = [(l[0], l[1] + 1, node(l[2], r[2]))]

    def emit_zeros(start, stop):
        while start < stop:
            remain = stop - start
            aligned_log = (start & -start).bit_length() - 1 if start else remain.bit_length() - 1
            h = min(remain.bit_length() - 1, aligned_log)
            push(start, h, empty_subtree(leaf_size, h, cache))
            start += 1 << h

    end = 0
    for i in sorted(occupied):
        digest = occupied[i]
        assert type(i) is int and end <= i < n and type(digest) is bytes and len(digest) == 32
        emit_zeros(end, i)
        push(i, 0, digest)
        end = i + 1
    emit_zeros(end, n)
    assert len(stack) == 1 and stack[0][1] == n.bit_length() - 1
    root = H(b'F' + size.to_bytes(8, 'big') + leaf_size.to_bytes(4, 'big') + stack[0][2])
    return root, pushes, len(cache)


def main():
    rng = random.Random(234567)
    for trial in range(512):
        leaf = rng.choice([1, 5, 4096, 65536])
        n = 1 << rng.randrange(0, 13)
        k = min(n, rng.randrange(60))
        hashes = {i: leaf_digest(rng.randbytes(leaf)) for i in rng.sample(range(n), k)}
        candidate = Collapsed(leaf * n, leaf, hashes)
        actual, pushes, zeros = independent_dyadic(leaf * n, leaf, hashes)
        assert candidate.root == actual, (trial, leaf, n, k)
        assert pushes >= k

    logical = 1 << 40  # no large array allocated; 16,777,216 logical 64KiB leaves
    leaf = 1 << 16
    last = logical // leaf - 1
    occupied = {
        7 * (1 << 30) // leaf: leaf_digest(b'a' * leaf),
        last: leaf_digest(b'Z' * leaf),
    }
    model = Collapsed(logical, leaf, occupied)
    independent, pushes, zeros = independent_dyadic(logical, leaf, occupied)
    assert model.root == independent
    assert pushes < 100 and zeros < 30
    print(json.dumps({
        'status':'PASS', 'posthoc_independent_dyadic_differentials':513,
        'logical_bytes':logical,'dyadic_block_pushes':pushes,
        'cached_zero_subtree_levels':zeros,
        'scope':'independent dyadic fold for power-of-two leaf counts, research not CMPCT product'
    },sort_keys=True))


if __name__ == '__main__':
    main()
