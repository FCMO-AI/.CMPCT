"""ONE-G0.2 descriptor-authentication arity prefilter v2.

Supersedes v1 without modifying it. The result-bearing v1 instrument had an implementation
defect: each per-leaf summary accidentally took maxima over the complete basis-leaf grid, so its
`retain_binary_descriptor_tree` result is invalid for scientific interpretation. This v2 changes
ONLY that grouping: a leaf summary is computed from rows having that exact `leaf_bytes`.

All preregistered science is otherwise unchanged: replay the exact successful binary descriptor-
tree rows; fixed candidate arities 3,4,5,8; exact stored-hash and proof-byte deltas; unchanged
independent-literal density requirement and <=1.20x median authenticated 4 KiB touch law. This is
still a cheap accounting falsifier, not authentication correctness evidence.

A non-binary arity survives only if at least one preregistered basis leaf beats independent
literals and satisfies the access gate on every matching row. Among survivors, select minimum
V=8 stored descriptor hashes, breaking ties by smaller V=8 proof. The selected arity must then
pass a full independent authentication/corruption A/B before promotion.
"""
from __future__ import annotations
import json, os
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import run as binary_run
from benchmarks.one.one_g02_shared_graph_auth_multiversion import LEAF_GRID, MAX_MEDIAN_TOUCH_AMP

HASH_BYTES = 32
ARITIES = (3, 4, 5, 8)


def _shape(n: int, arity: int) -> tuple[int, int]:
    widths = [n]
    while widths[-1] > 1:
        widths.append((widths[-1] + arity - 1) // arity)
    stored_nonroot = (sum(widths) - 1) * HASH_BYTES
    max_siblings = 0
    for index in range(n):
        width, current, siblings = n, index, 0
        while width > 1:
            start = (current // arity) * arity
            stop = min(start + arity, width)
            siblings += stop - start - 1
            current //= arity
            width = (width + arity - 1) // arity
        max_siblings = max(max_siblings, siblings)
    return stored_nonroot, max_siblings * HASH_BYTES


def run() -> dict[str, object]:
    base = binary_run()
    rows = base["results"]
    summaries = {}
    surviving = []
    for arity in ARITIES:
        by_leaf = {}
        for leaf in LEAF_GRID:
            adjusted = []
            for row in rows:
                if row["leaf_bytes"] != leaf:
                    continue
                stored, proof = _shape(row["version_count"], arity)
                persisted = row["candidate_persisted_bytes"] + stored - row["descriptor_tree_hash_bytes"]
                median_amp = row["median_authenticated_touch_amplification"] + (proof - row["descriptor_proof_bytes"]) / 4096
                max_amp = row["max_authenticated_touch_amplification"] + (proof - row["descriptor_proof_bytes"]) / 4096
                adjusted.append((persisted / row["literal_family_bytes"], median_amp, max_amp))
            by_leaf[str(leaf)] = {
                "max_candidate_fraction_of_literal_family": max(x[0] for x in adjusted),
                "max_row_median_touch_amplification": max(x[1] for x in adjusted),
                "max_touch_amplification": max(x[2] for x in adjusted),
                "passes_prefilter": max(x[0] for x in adjusted) < 1.0 and max(x[1] for x in adjusted) <= MAX_MEDIAN_TOUCH_AMP,
            }
        candidate_leaves = [int(k) for k,v in by_leaf.items() if v["passes_prefilter"]]
        v8_stored, v8_proof = _shape(8, arity)
        summaries[str(arity)] = {
            "candidate_leaves": candidate_leaves,
            "v8_stored_descriptor_hash_bytes": v8_stored,
            "v8_descriptor_proof_bytes": v8_proof,
            "leaf_summaries": by_leaf,
        }
        if candidate_leaves:
            surviving.append((v8_stored, v8_proof, arity))
    selected = min(surviving)[2] if surviving else None
    return {
        "schema":"cmpct-one-g02-descriptor-auth-arity-prefilter-v2",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "supersedes":"cmpct-one-g02-descriptor-auth-arity-prefilter-v1 due to cross-leaf grouping defect",
        "arities":list(ARITIES),
        "summaries":summaries,
        "selected_for_full_implementation":selected,
        "decision":"implement_selected_arity_for_full_auth_ab" if selected is not None else "retain_binary_descriptor_tree",
        "claim_boundary":"accounting prefilter only; non-binary authentication correctness and runtime are not established",
    }

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
