"""ONE-G0.2 authenticated-range alignment transfer falsifier.

Referee freeze before result-bearing execution
==============================================
The fixed-leaf authenticated range Pareto found a 2 KiB candidate on the original centered
4 KiB request. That request is exactly leaf-aligned for the candidate, so it does not yet
show that the density/access knee transfers to arbitrary byte ranges.

This experiment preserves the prior root sizes, request length, leaf grid, integrity model,
and thresholds. It changes only request alignment. For every leaf size, request starts sweep
all offsets modulo the leaf on a 64-byte grid plus the hostile final offset leaf_bytes-1.
The tree is built once per root/leaf; every proof is verified against exact requested bytes.

Frozen transfer gate: a leaf size transfers only if, at BOTH 64 KiB and 256 KiB roots,
(1) persistent index overhead is <=3.5%, (2) median authenticated bytes touched is <=1.20x,
and (3) every proof verifies exactly. No post-result alignment filtering or threshold search.
If no leaf transfers, preserve that as evidence that fixed reconstructed-root Merkle leaves
cannot satisfy the current generic density/access target under arbitrary alignment.
"""
from __future__ import annotations

import json
import os
import random
from statistics import median

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

ROOT_SIZES = (65_536, 262_144)
LEAF_BYTES = (1024, 2048, 4096, 8192, 16384)
REQUEST_BYTES = 4096
ALIGNMENT_STEP = 64
ROOT_SEED = 0xA17A11A11
MAX_INDEX_FRACTION = 0.035
MAX_MEDIAN_TOUCH_AMP = 1.20


def _alignment_offsets(leaf_bytes: int) -> tuple[int, ...]:
    values = list(range(0, leaf_bytes, ALIGNMENT_STEP))
    if leaf_bytes - 1 not in values:
        values.append(leaf_bytes - 1)
    return tuple(values)


def _start_for_mod(root_bytes: int, leaf_bytes: int, mod: int) -> int:
    center = (root_bytes - REQUEST_BYTES) // 2
    block = center - (center % leaf_bytes)
    start = block + mod
    if start + REQUEST_BYTES > root_bytes:
        start -= leaf_bytes
    if start < 0 or start + REQUEST_BYTES > root_bytes or start % leaf_bytes != mod:
        raise AssertionError("unable to realize frozen alignment")
    return start


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    summaries: dict[str, dict[str, object]] = {}
    failures: list[dict[str, object]] = []
    candidates: list[int] = []

    for root_bytes in ROOT_SIZES:
        data = random.Random(ROOT_SEED ^ root_bytes).randbytes(root_bytes)
        for leaf_bytes in LEAF_BYTES:
            tree = build_auth_tree(data, leaf_bytes)
            for mod in _alignment_offsets(leaf_bytes):
                start = _start_for_mod(root_bytes, leaf_bytes, mod)
                expected = data[start:start + REQUEST_BYTES]
                proof = prove_range(data, tree, start, REQUEST_BYTES)
                reasons: list[str] = []
                try:
                    got = verify_range(proof, tree.root, start, REQUEST_BYTES)
                    if got != expected:
                        reasons.append("verified_bytes_mismatch")
                except Exception as exc:
                    reasons.append(f"verification:{type(exc).__name__}")
                touched = proof.touched_data_bytes + proof.touched_proof_bytes
                row = {
                    "root_bytes": root_bytes,
                    "leaf_bytes": leaf_bytes,
                    "start_mod_leaf": mod,
                    "requested_bytes": REQUEST_BYTES,
                    "stored_index_bytes": tree.stored_index_bytes,
                    "stored_index_fraction_of_root": tree.stored_index_bytes / root_bytes,
                    "proof_hashes": len(proof.siblings),
                    "authenticated_leaf_payload_bytes": proof.touched_data_bytes,
                    "authenticated_bytes_touched": touched,
                    "authenticated_touch_amplification": touched / REQUEST_BYTES,
                    "failures": reasons,
                }
                rows.append(row)
                if reasons:
                    failures.append(row)

    for leaf_bytes in LEAF_BYTES:
        per_size: dict[str, object] = {}
        leaf_ok = True
        for root_bytes in ROOT_SIZES:
            group = [r for r in rows if r["root_bytes"] == root_bytes and r["leaf_bytes"] == leaf_bytes]
            amps = sorted(float(r["authenticated_touch_amplification"]) for r in group)
            p95 = amps[min(len(amps) - 1, int(0.95 * (len(amps) - 1)))]
            summary = {
                "rows": len(group),
                "index_fraction": float(group[0]["stored_index_fraction_of_root"]),
                "median_authenticated_touch_amplification": median(amps),
                "p95_authenticated_touch_amplification": p95,
                "max_authenticated_touch_amplification": max(amps),
            }
            per_size[str(root_bytes)] = summary
            if summary["index_fraction"] > MAX_INDEX_FRACTION or summary["median_authenticated_touch_amplification"] > MAX_MEDIAN_TOUCH_AMP:
                leaf_ok = False
        summaries[str(leaf_bytes)] = per_size
        if leaf_ok:
            candidates.append(leaf_bytes)

    return {
        "schema": "cmpct-one-g02-selective-auth-alignment-transfer-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "root_sizes": list(ROOT_SIZES),
        "request_bytes": REQUEST_BYTES,
        "leaf_grid_bytes": list(LEAF_BYTES),
        "alignment_step_bytes": ALIGNMENT_STEP,
        "rows": len(rows),
        "verification_failures": failures,
        "target_max_index_fraction": MAX_INDEX_FRACTION,
        "target_max_median_touch_amplification": MAX_MEDIAN_TOUCH_AMP,
        "target_candidates": candidates,
        "summaries": summaries,
        "decision": "fixed_leaf_auth_transfers_across_alignment" if candidates and not failures else "reject_fixed_reconstructed_root_leaf_knee_for_arbitrary_alignment",
        "claim_boundary": "research integrity/access transfer only; no canonical wire, product-speed, comparator or release authority",
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
