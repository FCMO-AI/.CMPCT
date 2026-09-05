"""ONE-G0.2 frozen binary-vs-quaternary descriptor-authentication compute A/B.

Referee freeze
==============
The exact structural A/B at source 50ed62ce selected quaternary descriptor authentication:
80-byte basis leaves are strictly smaller than independent literals on every frozen family row
while the worst row median authenticated 4 KiB touch remains <=1.20x.  Arity 4 removes stored
internal hashes but spends one extra 32-byte proof sibling at V=4/V=8.

Hypothesis: the shallower quaternary descriptor tree also removes enough hash work that the
structural win does not merely export cost into creation/selective verification CPU.

This instrument reuses the exact binary and quaternary implementations.  Inputs are generated
from the same frozen ONE-G0.2 version-family generator, then held immutable for both candidates.
It reports two layers:

1. deterministic SHA-256 operation/input-byte accounting for full descriptor build and one
   selective verification; and
2. repeated same-process CPython/hashlib wall time with alternating execution order, warmups,
   batched inner loops and medians.

The deterministic accounting is causal evidence; Python wall time is a research-runtime signal,
not native/product authority.  No density/access/security threshold may change after execution.

Frozen V=8 disproof/advance gate:
- binary and quaternary verification must remain exact on every generated case;
- quaternary must use fewer deterministic hash invocations for both build and selected verify;
- median full-build and selected-verify wall time ratios must each be <=1.05x binary;
- at least one of those two V=8 wall-time ratios must be <=0.90x.

If the gate fails, retain the structural density/access result but do not call quaternary an
execution-speed win; the next Builder must attack authentication ownership/implementation rather
than tuning arity or timing thresholds.
"""
from __future__ import annotations

import gc
import json
import os
import random
import time
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, MUTATIONS
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import (
    _build_desc_tree as build_binary,
    _desc_control,
    _desc_leaf,
    _desc_parent,
    _desc_proof,
    _verify_desc,
)
from benchmarks.one.one_g02_descriptor_auth_quaternary_ab import (
    _build as build_quaternary,
    _proof as proof_quaternary,
    _verify as verify_quaternary,
    _parent as qparent,
)

COUNTS = (4, 8)
FAMILIES_PER_ROOT = 3
REPETITIONS = 11
INNER_BUILD = 80
INNER_VERIFY = 120
MAX_SLOWDOWN = 1.05
MATERIAL_SPEEDUP = 0.90


def _families() -> list[tuple[int, int, list[bytes], list[bytes]]]:
    master = random.Random(MASTER_SEED ^ 0xA071FA11)
    out = []
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
                out.append((size, base_index, controls, blobs))
    return out


def _binary_parent_inputs(count: int) -> tuple[int, int]:
    """Return (parent hash ops, bytes fed to parent hashes) for full build."""
    width = count
    level = 1
    ops = 0
    input_bytes = 0
    while width > 1:
        parents = (width + 1) // 2
        ops += parents
        # _desc_parent: domain + u32 level + two 32-byte children.
        input_bytes += parents * (len(b"ONE-GDESC-P\0") + 4 + 64)
        width = parents
        level += 1
    return ops, input_bytes


def _quaternary_parent_inputs(count: int) -> tuple[int, int]:
    width = count
    ops = 0
    input_bytes = 0
    while width > 1:
        next_width = 0
        for start in range(0, width, 4):
            child_count = min(4, width - start)
            ops += 1
            input_bytes += len(b"ONE-GDESC-QP\0") + 8 + 32 * child_count
            next_width += 1
        width = next_width
    return ops, input_bytes


def _verify_accounting(blobs: list[bytes], *, quaternary: bool) -> dict[str, float]:
    ops = []
    bytes_in = []
    count = len(blobs)
    for index, blob in enumerate(blobs):
        # surprise digest + descriptor leaf are shared work.
        op = 2
        total = len(blob) + len(b"ONE-GDESC-L\0") + 4 + 40 + 32
        if quaternary:
            width = count
            cur = index
            while width > 1:
                start = (cur // 4) * 4
                child_count = min(4, width - start)
                op += 1
                total += len(b"ONE-GDESC-QP\0") + 8 + 32 * child_count
                cur //= 4
                width = (width + 3) // 4
        else:
            width = count
            cur = index
            while width > 1:
                op += 1
                total += len(b"ONE-GDESC-P\0") + 4 + 64
                cur //= 2
                width = (width + 1) // 2
        ops.append(op)
        bytes_in.append(total)
    return {
        "median_hash_ops": median(ops),
        "max_hash_ops": max(ops),
        "median_hash_input_bytes": median(bytes_in),
        "max_hash_input_bytes": max(bytes_in),
    }


def _build_accounting(blobs: list[bytes], *, quaternary: bool) -> dict[str, int]:
    count = len(blobs)
    parent_ops, parent_bytes = (
        _quaternary_parent_inputs(count) if quaternary else _binary_parent_inputs(count)
    )
    leaf_input = len(b"ONE-GDESC-L\0") + 4 + 40 + 32
    # Each version hashes its complete Surprise once, then hashes the descriptor leaf.
    return {
        "hash_ops": 2 * count + parent_ops,
        "hash_input_bytes": sum(len(b) for b in blobs) + count * leaf_input + parent_bytes,
        "parent_hash_ops": parent_ops,
        "parent_hash_input_bytes": parent_bytes,
    }


def _timed(fn, inner: int) -> int:
    start = time.perf_counter_ns()
    for _ in range(inner):
        fn()
    return time.perf_counter_ns() - start


def _measure_pair(binary_fn, quaternary_fn, inner: int) -> tuple[float, float, list[int], list[int]]:
    # Warm both paths before measurement; alternate order to reduce drift bias.
    for _ in range(3):
        binary_fn(); quaternary_fn()
    b = []
    q = []
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        for rep in range(REPETITIONS):
            if rep % 2 == 0:
                b.append(_timed(binary_fn, inner)); q.append(_timed(quaternary_fn, inner))
            else:
                q.append(_timed(quaternary_fn, inner)); b.append(_timed(binary_fn, inner))
    finally:
        if was_enabled:
            gc.enable()
    return median(b), median(q), b, q


def run() -> dict[str, object]:
    rows = []
    exact_failures = []
    for root_size, base_index, controls, blobs in _families():
        count = len(blobs)
        binary_tree = build_binary(controls, blobs)
        qtree = build_quaternary(controls, blobs)
        binary_proofs = [_desc_proof(binary_tree, i) for i in range(count)]
        qproofs = [proof_quaternary(qtree, i) for i in range(count)]

        def verify_binary_all() -> None:
            for i in range(count):
                _verify_desc(index=i, count=count, control=controls[i], surprise=blobs[i],
                             proof=binary_proofs[i], expected_root=binary_tree.root)

        def verify_q_all() -> None:
            for i in range(count):
                verify_quaternary(i, count, controls[i], blobs[i], qproofs[i], qtree.root)

        try:
            verify_binary_all(); verify_q_all()
        except Exception as exc:
            exact_failures.append({"root": root_size, "base": base_index, "count": count,
                                   "reason": type(exc).__name__})

        b_build, q_build, b_build_raw, q_build_raw = _measure_pair(
            lambda: build_binary(controls, blobs), lambda: build_quaternary(controls, blobs), INNER_BUILD
        )
        b_verify, q_verify, b_verify_raw, q_verify_raw = _measure_pair(
            verify_binary_all, verify_q_all, INNER_VERIFY
        )
        rows.append({
            "root_size": root_size,
            "base_index": base_index,
            "version_count": count,
            "surprise_bytes": sum(len(x) for x in blobs),
            "binary_persisted_hash_bytes": binary_tree.stored_nonroot_hash_bytes,
            "quaternary_persisted_hash_bytes": qtree.stored_nonroot_hash_bytes,
            "binary_max_proof_bytes": max(32 * len(p) for p in binary_proofs),
            "quaternary_max_proof_bytes": max(sum(len(s) for _, _, _, s in p) * 32 for p in qproofs),
            "binary_build_accounting": _build_accounting(blobs, quaternary=False),
            "quaternary_build_accounting": _build_accounting(blobs, quaternary=True),
            "binary_verify_accounting": _verify_accounting(blobs, quaternary=False),
            "quaternary_verify_accounting": _verify_accounting(blobs, quaternary=True),
            "binary_build_median_ns": b_build,
            "quaternary_build_median_ns": q_build,
            "build_ratio": q_build / b_build,
            "binary_verify_all_median_ns": b_verify,
            "quaternary_verify_all_median_ns": q_verify,
            "verify_ratio": q_verify / b_verify,
            "raw_batch_ns": {"binary_build": b_build_raw, "quaternary_build": q_build_raw,
                             "binary_verify": b_verify_raw, "quaternary_verify": q_verify_raw},
        })

    summaries = {}
    for count in COUNTS:
        group = [r for r in rows if r["version_count"] == count]
        summaries[str(count)] = {
            "median_build_ratio": median(r["build_ratio"] for r in group),
            "max_build_ratio": max(r["build_ratio"] for r in group),
            "median_verify_ratio": median(r["verify_ratio"] for r in group),
            "max_verify_ratio": max(r["verify_ratio"] for r in group),
            "binary_build_hash_ops": group[0]["binary_build_accounting"]["hash_ops"],
            "quaternary_build_hash_ops": group[0]["quaternary_build_accounting"]["hash_ops"],
            "binary_verify_median_hash_ops": group[0]["binary_verify_accounting"]["median_hash_ops"],
            "quaternary_verify_median_hash_ops": group[0]["quaternary_verify_accounting"]["median_hash_ops"],
        }

    v8 = summaries["8"]
    deterministic_better = (
        v8["quaternary_build_hash_ops"] < v8["binary_build_hash_ops"]
        and v8["quaternary_verify_median_hash_ops"] < v8["binary_verify_median_hash_ops"]
    )
    timing_bounded = v8["median_build_ratio"] <= MAX_SLOWDOWN and v8["median_verify_ratio"] <= MAX_SLOWDOWN
    material = min(v8["median_build_ratio"], v8["median_verify_ratio"]) <= MATERIAL_SPEEDUP
    passed = not exact_failures and deterministic_better and timing_bounded and material
    return {
        "schema": "cmpct-one-g02-descriptor-auth-quaternary-compute-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "frozen_gate": {"max_v8_median_slowdown_ratio": MAX_SLOWDOWN,
                        "material_speedup_ratio": MATERIAL_SPEEDUP},
        "exact_failures": exact_failures,
        "summaries": summaries,
        "rows": rows,
        "decision": "advance_quaternary_compute_shape" if passed else "quaternary_compute_not_proven",
        "claim_boundary": "deterministic SHA work + CPython/hashlib same-runner timing; no native/product/release authority",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
