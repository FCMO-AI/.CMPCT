"""ONE-G0.2 generic authenticated-range Crystallization Pareto.

Referee freeze
==============
The generic range-cone Builder reduced decoded-Program reconstruction to 2x, but its range
was deliberately unauthenticated. This experiment asks whether a generic stored hash tree
can make the same 4 KiB request independently authenticatable without paying either a large
persistent density tax or source-size-proportional proof traffic.

All tree hashes are physically charged. The root digest replaces the existing 32-byte root
SHA; the sidecar charges a 4-byte leaf-size field plus every non-root tree hash. Proof hashes
are not gifted. Full leaf payloads intersecting the request are charged because a verifier
must hash complete authenticated leaves. This is an integrity/index experiment only; it does
not claim the current ONE wire can yet seek directly to these bytes.

Frozen leaf grid: 1, 2, 4, 8, 16 KiB. No post-result threshold search.
Decision-changing target: identify whether any fixed generic point simultaneously achieves
<=3.5% persistent integrity-index overhead and <=1.20x median authenticated bytes touched
(request leaf payload + proof hashes) at BOTH 64 KiB and 256 KiB source sizes, with exact
verification on every row. If none does, preserve the Pareto as a negative constraint.
"""
from __future__ import annotations

import json
import os
import random
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, MUTATION_COUNTS, _edited,
)
from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

REQUEST_BYTES = 4096
LEAF_BYTES = (1024, 2048, 4096, 8192, 16384)
MAX_INDEX_FRACTION = 0.035
MAX_TOUCH_AMP = 1.20


def run():
    master = random.Random(MASTER_SEED)
    rows = []
    failures = []
    groups = {(size, leaf): [] for size in BASE_SIZES for leaf in LEAF_BYTES}
    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            for mutations in MUTATION_COUNTS:
                edited = _edited(base, random.Random(seed ^ (mutations << 32) ^ 0xA11CE5EED), mutations)
                start = (size - REQUEST_BYTES) // 2
                expected = edited[start:start + REQUEST_BYTES]
                for leaf in LEAF_BYTES:
                    tree = build_auth_tree(edited, leaf)
                    proof = prove_range(edited, tree, start, REQUEST_BYTES)
                    reasons = []
                    try:
                        got = verify_range(proof, tree.root, start, REQUEST_BYTES)
                        if got != expected:
                            reasons.append("verified_bytes_mismatch")
                    except Exception as exc:
                        reasons.append(f"verification:{type(exc).__name__}")
                    touched = proof.touched_data_bytes + proof.touched_proof_bytes
                    row = {
                        "base_bytes": size,
                        "base_index": base_index,
                        "mutation_count": mutations,
                        "leaf_bytes": leaf,
                        "requested_bytes": REQUEST_BYTES,
                        "stored_index_bytes": tree.stored_index_bytes,
                        "stored_index_fraction_of_root": tree.stored_index_bytes / size,
                        "proof_hashes": len(proof.siblings),
                        "proof_hash_bytes": proof.touched_proof_bytes,
                        "authenticated_leaf_payload_bytes": proof.touched_data_bytes,
                        "authenticated_bytes_touched": touched,
                        "authenticated_touch_amplification": touched / REQUEST_BYTES,
                        "failures": reasons,
                    }
                    rows.append(row)
                    groups[(size, leaf)].append(row)
                    if reasons:
                        failures.append(row)

    summaries = {}
    candidates = []
    for leaf in LEAF_BYTES:
        leaf_ok = True
        per_size = {}
        for size in BASE_SIZES:
            group = groups[(size, leaf)]
            s = {
                "rows": len(group),
                "median_index_fraction": median(r["stored_index_fraction_of_root"] for r in group),
                "median_authenticated_touch_amplification": median(r["authenticated_touch_amplification"] for r in group),
                "max_authenticated_touch_amplification": max(r["authenticated_touch_amplification"] for r in group),
                "median_proof_hashes": median(r["proof_hashes"] for r in group),
            }
            per_size[str(size)] = s
            if s["median_index_fraction"] > MAX_INDEX_FRACTION or s["median_authenticated_touch_amplification"] > MAX_TOUCH_AMP:
                leaf_ok = False
        summaries[str(leaf)] = per_size
        if leaf_ok:
            candidates.append(leaf)

    return {
        "schema": "cmpct-one-g02-selective-auth-tree-pareto-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "request_bytes": REQUEST_BYTES,
        "leaf_grid_bytes": list(LEAF_BYTES),
        "rows": len(rows),
        "verification_failures": failures,
        "target_max_index_fraction": MAX_INDEX_FRACTION,
        "target_max_touch_amplification": MAX_TOUCH_AMP,
        "target_candidates": candidates,
        "summaries": summaries,
        "decision": "generic_authenticated_crystallization_has_feasible_knee" if candidates and not failures else "preserve_auth_density_access_tradeoff_negative",
        "remaining_debt": ["physical_wire_seek/index integration", "creation CPU and native hash throughput", "failure-blast-radius and update-cost validation"],
        "claim_boundary": "research authenticated-index economics only; not canonical wire, product speed, comparator or release authority",
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
