"""ONE-G0.2 packed quaternary descriptor-proof execution-debt rehabilitation.

Referee freeze before result-bearing execution
==============================================
The exact quaternary structural A/B advanced arity 4, but the subsequent compute A/B found
V=8 reference verification ~15.9% slower than binary despite fewer SHA calls/input bytes.
Inspection identifies reader-side representational overhead that is not information: the current
research proof stores `(level, slot, child_count, ((sibling_slot,digest),...))`, even though
level, slot and child_count are deterministic functions of the requested descriptor index,
version count and current tree width.

Hypothesis: canonicalize each quaternary proof level to ONLY its sibling digests, concatenated in
child order with the current child omitted.  The reader reconstructs the complete child byte
sequence by inserting the running digest at the derived slot.  This changes no authenticated
information, no digest/proof byte count, no hash domains and no tree root; it removes redundant
in-memory control structure from the reference verifier.

Frozen inputs are identical to the prior binary-vs-quaternary compute A/B: V=4/V=8, three
families at each 64 KiB/256 KiB root size.  Old and packed proofs are generated from the exact
same already-frozen QTree.  Every packed verification must equal the old root and deterministic
proof corruption must reject.  Timing uses same-process warmup, alternating old/packed order,
batched inner loops, disabled GC and 15 medians.

Frozen V=8 advancement gate:
- zero exact/corruption failures;
- packed proof digest bytes must equal old proof digest bytes on every row;
- median packed/old verification ratio <=0.92x;
- median packed/binary verification ratio <=1.05x, using the exact binary verifier;
- no V=4 row may exceed 1.05x old quaternary.
If it fails, do not tune thresholds; preserve the negative and let the native discriminator
separate interpreter overhead from authentication geometry.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import random
import struct
import time
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, MUTATIONS
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import (
    _build_desc_tree as _build_binary,
    _desc_control,
    _desc_proof as _binary_proof,
    _verify_desc as _verify_binary,
)
from benchmarks.one.one_g02_descriptor_auth_quaternary_ab import (
    ARITY, HASH_BYTES, PARENT_DOMAIN, _build as _build_q, _proof as _old_proof, _verify as _old_verify,
)

COUNTS = (4, 8)
FAMILIES_PER_ROOT = 3
REPETITIONS = 15
INNER = 140
MAX_OLD_RATIO = 0.92
MAX_BINARY_RATIO = 1.05
MAX_V4_ROW_RATIO = 1.05


def _families():
    master = random.Random(MASTER_SEED ^ 0xA071FA11)
    for size in ROOT_SIZES:
        for base_index in range(FAMILIES_PER_ROOT):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            surprises = []
            for m in MUTATIONS:
                edited = _edited(base, random.Random(seed ^ (m << 32) ^ 0xA11CE5EED), m)
                blob, _ = _surprise_blob(base, edited)
                surprises.append(blob)
            for count in COUNTS:
                blobs = surprises[:count]
                controls = [_desc_control(i, blobs[i]) for i in range(count)]
                yield size, base_index, controls, blobs


def _packed_proof(tree, index: int) -> tuple[bytes, ...]:
    out = []
    cur = index
    for level in tree.levels[:-1]:
        start = (cur // ARITY) * ARITY
        stop = min(start + ARITY, len(level))
        out.append(b"".join(level[i] for i in range(start, stop) if i != cur))
        cur //= ARITY
    return tuple(out)


def _verify_packed(index: int, count: int, control: bytes, surprise: bytes,
                   proof: tuple[bytes, ...], root: bytes) -> None:
    if index < 0 or index >= count:
        raise ValueError("index")
    # Exact existing leaf domain/grammar.
    from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import _desc_leaf
    h = _desc_leaf(index, control, hashlib.sha256(surprise).digest())
    cur, width = index, count
    expected_levels = 0
    w = width
    while w > 1:
        expected_levels += 1
        w = (w + ARITY - 1) // ARITY
    if len(proof) != expected_levels:
        raise ValueError("proof depth")
    for level_no, siblings in enumerate(proof):
        start = (cur // ARITY) * ARITY
        child_count = min(ARITY, width - start)
        slot = cur - start
        expected = (child_count - 1) * HASH_BYTES
        if len(siblings) != expected:
            raise ValueError("proof sibling bytes")
        split = slot * HASH_BYTES
        child_bytes = siblings[:split] + h + siblings[split:]
        if len(child_bytes) != child_count * HASH_BYTES:
            raise ValueError("proof geometry")
        h = hashlib.sha256(
            PARENT_DOMAIN + struct.pack("<II", level_no + 1, child_count) + child_bytes
        ).digest()
        cur //= ARITY
        width = (width + ARITY - 1) // ARITY
    if h != root:
        raise ValueError("descriptor authentication failed")


def _time(fn) -> int:
    start = time.perf_counter_ns()
    for _ in range(INNER):
        fn()
    return time.perf_counter_ns() - start


def _measure(old_fn, packed_fn, binary_fn):
    for _ in range(3):
        old_fn(); packed_fn(); binary_fn()
    old, packed, binary = [], [], []
    enabled = gc.isenabled(); gc.disable()
    try:
        for rep in range(REPETITIONS):
            if rep & 1:
                packed.append(_time(packed_fn)); old.append(_time(old_fn)); binary.append(_time(binary_fn))
            else:
                old.append(_time(old_fn)); packed.append(_time(packed_fn)); binary.append(_time(binary_fn))
    finally:
        if enabled: gc.enable()
    return median(old), median(packed), median(binary)


def run() -> dict[str, object]:
    rows = []
    exact_failures = []
    corruption_failures = []
    byte_mismatches = []
    for root_size, base_index, controls, blobs in _families():
        count = len(blobs)
        qt = _build_q(controls, blobs)
        bt = _build_binary(controls, blobs)
        old = [_old_proof(qt, i) for i in range(count)]
        packed = [_packed_proof(qt, i) for i in range(count)]
        binary = [_binary_proof(bt, i) for i in range(count)]
        for i in range(count):
            old_bytes = sum(len(sibs) for _, _, _, sibs in old[i]) * HASH_BYTES
            packed_bytes = sum(len(x) for x in packed[i])
            if old_bytes != packed_bytes:
                byte_mismatches.append({"root": root_size, "base": base_index, "count": count,
                                        "version": i, "old": old_bytes, "packed": packed_bytes})
            try:
                _old_verify(i, count, controls[i], blobs[i], old[i], qt.root)
                _verify_packed(i, count, controls[i], blobs[i], packed[i], qt.root)
                _verify_binary(index=i, count=count, control=controls[i], surprise=blobs[i],
                               proof=binary[i], expected_root=bt.root)
            except Exception as exc:
                exact_failures.append({"root": root_size, "base": base_index, "count": count,
                                       "version": i, "reason": type(exc).__name__})
            if packed[i] and packed[i][0]:
                bad = list(packed[i]); b = bytearray(bad[0]); b[0] ^= 1; bad[0] = bytes(b)
                try:
                    _verify_packed(i, count, controls[i], blobs[i], tuple(bad), qt.root)
                    corruption_failures.append({"root": root_size, "base": base_index,
                                                "count": count, "version": i})
                except ValueError:
                    pass

        def old_all():
            for i in range(count): _old_verify(i, count, controls[i], blobs[i], old[i], qt.root)
        def packed_all():
            for i in range(count): _verify_packed(i, count, controls[i], blobs[i], packed[i], qt.root)
        def binary_all():
            for i in range(count): _verify_binary(index=i, count=count, control=controls[i],
                                                  surprise=blobs[i], proof=binary[i], expected_root=bt.root)
        om, pm, bm = _measure(old_all, packed_all, binary_all)
        rows.append({
            "root_size": root_size, "base_index": base_index, "version_count": count,
            "surprise_bytes": sum(len(x) for x in blobs),
            "old_quaternary_median_ns": om, "packed_quaternary_median_ns": pm,
            "binary_median_ns": bm, "packed_vs_old_ratio": pm / om,
            "packed_vs_binary_ratio": pm / bm,
            "proof_bytes": max(sum(len(x) for x in p) for p in packed),
        })

    summaries = {}
    for count in COUNTS:
        group = [r for r in rows if r["version_count"] == count]
        summaries[str(count)] = {
            "median_packed_vs_old_ratio": median(r["packed_vs_old_ratio"] for r in group),
            "max_packed_vs_old_ratio": max(r["packed_vs_old_ratio"] for r in group),
            "median_packed_vs_binary_ratio": median(r["packed_vs_binary_ratio"] for r in group),
            "max_packed_vs_binary_ratio": max(r["packed_vs_binary_ratio"] for r in group),
        }
    v8 = summaries["8"]
    passes = (
        not exact_failures and not corruption_failures and not byte_mismatches
        and v8["median_packed_vs_old_ratio"] <= MAX_OLD_RATIO
        and v8["median_packed_vs_binary_ratio"] <= MAX_BINARY_RATIO
        and summaries["4"]["max_packed_vs_old_ratio"] <= MAX_V4_ROW_RATIO
    )
    return {
        "schema": "cmpct-one-g02-descriptor-auth-packed-proof-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "frozen_gate": {"max_v8_packed_vs_old": MAX_OLD_RATIO,
                        "max_v8_packed_vs_binary": MAX_BINARY_RATIO,
                        "max_v4_row_packed_vs_old": MAX_V4_ROW_RATIO},
        "exact_failures": exact_failures,
        "corruption_failures": corruption_failures,
        "proof_byte_mismatches": byte_mismatches,
        "summaries": summaries,
        "rows": rows,
        "decision": "advance_packed_quaternary_proof" if passes else "packed_proof_speed_gate_failed",
        "claim_boundary": "same authenticated digest bytes/root; CPython reference verifier rehabilitation only; no native/product/release authority",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
