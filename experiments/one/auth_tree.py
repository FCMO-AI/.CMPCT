"""Research-only generic authenticated range tree for ONE-G0.2.

This is not a canonical wire-format change.  It models one possible generic integrity
Crystallization so selective reads can be authenticated without a whole-root scan.
Every stored hash is charged by callers; no proof is gifted.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import ceil
import struct


HASH_BYTES = 32


def _leaf_hash(index: int, total_len: int, payload: bytes) -> bytes:
    return sha256(b"ONE-L\x00" + struct.pack("<QQ", index, total_len) + payload).digest()


def _parent_hash(level: int, left: bytes, right: bytes) -> bytes:
    return sha256(b"ONE-P\x00" + struct.pack("<I", level) + left + right).digest()


def _root_commit(total_len: int, leaf_bytes: int, tree_root: bytes) -> bytes:
    return sha256(b"ONE-R\x00" + struct.pack("<QI", total_len, leaf_bytes) + tree_root).digest()


@dataclass(frozen=True)
class AuthTree:
    total_len: int
    leaf_bytes: int
    levels: tuple[tuple[bytes, ...], ...]
    root: bytes

    @property
    def leaf_count(self) -> int:
        return len(self.levels[0])

    @property
    def stored_index_bytes(self) -> int:
        # Root digest replaces the existing 32-byte whole-root digest.  The generic
        # sidecar needs leaf-size metadata plus every non-root tree hash. Level geometry
        # is derivable from total_len + leaf_bytes, so offsets need no per-hash metadata.
        hashes = sum(len(level) for level in self.levels) - 1
        return 4 + HASH_BYTES * hashes


@dataclass(frozen=True)
class RangeProof:
    total_len: int
    leaf_bytes: int
    first_leaf: int
    leaf_payloads: tuple[bytes, ...]
    siblings: tuple[tuple[int, int, bytes], ...]  # (level,index,digest)

    @property
    def touched_data_bytes(self) -> int:
        return sum(len(x) for x in self.leaf_payloads)

    @property
    def touched_proof_bytes(self) -> int:
        # Coordinates are not charged as stored bytes: fixed tree geometry + requested
        # range determines exactly which sibling offsets are needed. Only hash bytes move.
        return HASH_BYTES * len(self.siblings)


def build_auth_tree(data: bytes, leaf_bytes: int) -> AuthTree:
    if type(leaf_bytes) is not int or leaf_bytes <= 0:
        raise ValueError("leaf_bytes must be positive integer")
    total = len(data)
    count = max(1, ceil(total / leaf_bytes))
    leaves = tuple(_leaf_hash(i, total, data[i*leaf_bytes:min(total,(i+1)*leaf_bytes)]) for i in range(count))
    levels = [leaves]
    level_no = 1
    current = leaves
    while len(current) > 1:
        nxt = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i+1] if i+1 < len(current) else left
            nxt.append(_parent_hash(level_no, left, right))
        current = tuple(nxt)
        levels.append(current)
        level_no += 1
    return AuthTree(total, leaf_bytes, tuple(levels), _root_commit(total, leaf_bytes, current[0]))


def prove_range(data: bytes, tree: AuthTree, start: int, length: int) -> RangeProof:
    if start < 0 or length < 0 or start + length > len(data) or len(data) != tree.total_len:
        raise ValueError("invalid proof range")
    if length == 0:
        first = min(start // tree.leaf_bytes, tree.leaf_count - 1)
        selected = {first}
    else:
        first = start // tree.leaf_bytes
        last = (start + length - 1) // tree.leaf_bytes
        selected = set(range(first, last + 1))
    payloads = tuple(data[i*tree.leaf_bytes:min(len(data),(i+1)*tree.leaf_bytes)] for i in sorted(selected))
    siblings = []
    current = set(selected)
    for level_no, level in enumerate(tree.levels[:-1]):
        needed = set()
        for idx in current:
            sib = idx ^ 1
            if sib < len(level) and sib not in current:
                needed.add(sib)
        for idx in sorted(needed):
            siblings.append((level_no, idx, level[idx]))
        current = {idx // 2 for idx in current}
    return RangeProof(tree.total_len, tree.leaf_bytes, first, payloads, tuple(siblings))


def verify_range(proof: RangeProof, expected_root: bytes, start: int, length: int) -> bytes:
    if len(expected_root) != HASH_BYTES or start < 0 or length < 0 or start + length > proof.total_len:
        raise ValueError("invalid verification request")
    nodes: dict[tuple[int,int], bytes] = {}
    for off, payload in enumerate(proof.leaf_payloads):
        idx = proof.first_leaf + off
        nodes[(0, idx)] = _leaf_hash(idx, proof.total_len, payload)
    for level, idx, digest in proof.siblings:
        if len(digest) != HASH_BYTES:
            raise ValueError("bad proof hash")
        nodes[(level, idx)] = digest
    level_no = 0
    width = max(1, ceil(proof.total_len / proof.leaf_bytes))
    while width > 1:
        parents = set(idx // 2 for (level, idx) in nodes if level == level_no)
        for parent in sorted(parents):
            li = 2 * parent; ri = li + 1
            left = nodes.get((level_no, li))
            right = nodes.get((level_no, ri))
            if right is None and ri >= width:
                right = left
            if left is not None and right is not None:
                nodes[(level_no + 1, parent)] = _parent_hash(level_no + 1, left, right)
        width = (width + 1) // 2
        level_no += 1
    tree_root = nodes.get((level_no, 0))
    if tree_root is None or _root_commit(proof.total_len, proof.leaf_bytes, tree_root) != expected_root:
        raise ValueError("range authentication failed")
    joined = b"".join(proof.leaf_payloads)
    leaf_origin = proof.first_leaf * proof.leaf_bytes
    rel = start - leaf_origin
    out = joined[rel:rel+length]
    if len(out) != length:
        raise ValueError("proof does not cover requested range")
    return out
