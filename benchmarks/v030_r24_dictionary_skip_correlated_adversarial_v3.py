from __future__ import annotations

"""Correlated positive-sample disproof surface for the r24 dictionary-training skip.

The v2 campaign finally exercised the real trainer on unseen large high-entropy text and found exact byte identity
plus material speedups.  That is necessary but not sufficient for a generic pre-training skip rule: dictionaries
exist specifically to exploit redundancy *between* samples.  A rule based only on file/sample counts must therefore
also survive large correlated members that evade micro-packing and give the trainer a realistic chance to win codec
competition.

This v3 wrapper preserves every v1/v2 case and adds two independently seeded families. Each file is larger than the
release micro-pack ceiling and contains one shared random prefix plus an independent high-entropy tail.  The shared
prefix is intentionally close to the 24 KiB dictionary budget, making these cases a direct adversarial test of the
claimed "training can be skipped without changing bytes" property rather than another abstention case.

Production policy is not changed by this oracle. Any non-exact admission is a counterexample and blocks the broad
rule; a narrower replacement may be considered only if it is expressed in generic pre-training features and still
covers material frozen + unseen opportunities.
"""

import argparse
import json
from pathlib import Path
import random

from benchmarks import v030_r24_dictionary_skip_adversarial_v2 as V2
from benchmarks import v030_r24_dictionary_skip_adversarial_oracle as V1

SCHEMA = "cmpct-v030-r24-dictionary-skip-correlated-adversarial-v3"
ADDITIONAL_CORRELATED_CASES = 2
CORRELATED_LABELS = {
    "adversarial/large_shared_prefix_40",
    "adversarial/large_shared_prefix_64",
}

_ORIGINAL_V2_BUILD = V2._build_v2_adversarial


def _build_v3_adversarial(root: Path):
    cases = list(_ORIGINAL_V2_BUILD(root))
    rng = random.Random(V1.SEED ^ 0xC011A7ED)

    case = root / "large_shared_prefix_40"
    shared = bytes(rng.getrandbits(8) for _ in range(24 * 1024))
    for i in range(40):
        tail = bytes(rng.getrandbits(8) for _ in range(288 * 1024 + (i % 5) * 4096))
        path = case / f"shared-{i:03d}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(shared + tail)
    cases.append((case.name, case, V1._tree_provenance(case)))

    case = root / "large_shared_prefix_64"
    shared = bytes(rng.getrandbits(8) for _ in range(32 * 1024))
    for i in range(64):
        tail = bytes(rng.getrandbits(8) for _ in range(320 * 1024 + (i % 7) * 4096))
        path = case / f"correlated-{i:03d}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(shared + tail)
    cases.append((case.name, case, V1._tree_provenance(case)))
    return cases


def _matches_broad_v2_rule(row: dict) -> bool:
    features = row["pretraining_features"]
    return int(features["regular_files"]) >= 5 and int(features["dictionary_sample_count"]) >= 32


def run(work_root: Path) -> dict:
    original = V2._build_v2_adversarial
    V2._build_v2_adversarial = _build_v3_adversarial
    try:
        result = dict(V2.run(work_root))
    finally:
        V2._build_v2_adversarial = original

    result["schema"] = SCHEMA
    contract = dict(result["contract"])
    contract.update(
        {
            "additional_correlated_positive_sample_cases": ADDITIONAL_CORRELATED_CASES,
            "correlated_case_design": "shared-24-32kib-random-prefix-plus-independent-high-entropy-tail",
            "broad_v2_rule_under_test": {
                "regular_files_min": 5,
                "dictionary_sample_count_min": 32,
            },
            "correlated_nonexact_admission_blocks_broad_rule": True,
            "production_change": False,
            "release_credit": False,
        }
    )
    result["contract"] = contract

    correlated_rows = [row for row in result["adversarial_rows"] if row["label"] in CORRELATED_LABELS]
    broad_admissions = [row for row in result["adversarial_rows"] if _matches_broad_v2_rule(row)]
    broad_counterexamples = [
        row
        for row in broad_admissions
        if not bool(row["measurement"]["exact_archive_bytes_and_sha"])
        or not bool(row["measurement"]["canonical_product_tree_equal"])
        or float(row["measurement"]["saved_s"]) < 0.005
    ]

    summary = dict(result["summary"])
    summary.update(
        {
            "correlated_surface_complete": len(correlated_rows) == ADDITIONAL_CORRELATED_CASES,
            "correlated_training_surface_exercised": all(
                int(row["pretraining_features"]["dictionary_sample_count"]) >= 32 for row in correlated_rows
            ),
            "broad_v2_rule_admissions": len(broad_admissions),
            "broad_v2_rule_counterexamples": len(broad_counterexamples),
            "broad_v2_rule_survives": bool(broad_admissions) and not broad_counterexamples,
            "broad_v2_rule_counterexample_labels": [row["label"] for row in broad_counterexamples],
        }
    )
    result["summary"] = summary
    result["correlated_rows"] = correlated_rows
    result["broad_v2_rule_counterexamples"] = broad_counterexamples
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only correlated large-text disproof surface. The currently evidenced broad pre-training rule may "
        "be promoted only if every admitted correlated case remains byte-identical, tree-identical and saves at "
        "least 5 ms. Any counterexample is preserved and blocks that broad rule; thresholds may not be moved after "
        "observing these outcomes."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-dictionary-skip-correlated-v3-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-dictionary-skip-correlated-v3.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True), flush=True)

    if not result["summary"]["correlated_surface_complete"]:
        raise SystemExit("dictionary-skip v3 did not execute the complete correlated disproof surface")
    if not result["summary"]["correlated_training_surface_exercised"]:
        raise SystemExit("dictionary-skip v3 correlated cases did not exercise >=32 real training samples")


if __name__ == "__main__":
    main()
