from __future__ import annotations

"""Positive-unseen extension of the r24 dictionary-skip generalization campaign.

The v1 adversarial surface is useful negative evidence, but all seven generated trees currently
produce zero dictionary-training samples after the real release scan/micro-pack preparation.  That
means a frozen-suite rule can survive v1 merely by abstaining on every unseen case: safe, but not
positive generalization evidence.

This wrapper preserves every v1 case and adds two independently seeded large-text entropy families
whose members are deliberately too large for the tiny-file/micro-pack path.  The real
``_pretraining_features`` implementation must therefore prove that the release trainer sees a
non-empty (and for promotion, >=32-sample) training surface.  Candidate admission still uses only
generic pre-training features; workload names, paths and hashes remain forbidden.

Production is unchanged.  Even a positive result is promotion evidence only and still requires a
separate shipping regression plus the ordinary external/no-regression/runtime/native/Android gates.
"""

import argparse
import json
from pathlib import Path
import random

from benchmarks import v030_r24_dictionary_skip_adversarial_oracle as V1

SCHEMA = "cmpct-v030-r24-dictionary-skip-adversarial-v2"
ADDITIONAL_CASES = 2
MIN_POSITIVE_SAMPLE_COUNT = 32
MIN_POSITIVE_SAVED_S = 0.005


def _build_v2_adversarial(root: Path):
    cases = list(_ORIGINAL_BUILD(root))
    rng = random.Random(V1.SEED ^ 0x5A17C0DE)

    # Independent high-entropy text family.  Large members intentionally avoid the tiny/micro-pack
    # path so the actual release dictionary sampler—not a synthetic proxy—must see the files.
    case = root / "large_entropy_text_40"
    for i in range(40):
        V1._write_random(
            case / f"segment-{i:03d}.txt",
            size=768 * 1024 + (i % 7) * 8192,
            rng=rng,
        )
    cases.append((case.name, case, V1._tree_provenance(case)))

    # Different count, size distribution and seed.  This prevents one favorable training cardinality
    # from being mistaken for a generalized rule.
    case = root / "large_entropy_text_64"
    for i in range(64):
        V1._write_random(
            case / f"record-{i:03d}.txt",
            size=512 * 1024 + (i % 11) * 4096,
            rng=rng,
        )
    cases.append((case.name, case, V1._tree_provenance(case)))
    return cases


_ORIGINAL_BUILD = V1._build_adversarial


def run(work_root: Path) -> dict:
    V1._build_adversarial = _build_v2_adversarial
    try:
        result = dict(V1.run(work_root))
    finally:
        V1._build_adversarial = _ORIGINAL_BUILD

    result["schema"] = SCHEMA
    contract = dict(result["contract"])
    contract.update(
        {
            "adversarial_cases": len(result["adversarial_rows"]),
            "v1_adversarial_cases_preserved": 7,
            "additional_positive_unseen_cases": ADDITIONAL_CASES,
            "minimum_positive_training_sample_count": MIN_POSITIVE_SAMPLE_COUNT,
            "positive_training_surface_required_for_promotion_signal": True,
            "positive_unseen_saved_time_required_s": MIN_POSITIVE_SAVED_S,
            "production_change": False,
            "release_credit": False,
        }
    )
    result["contract"] = contract

    training_rows = [
        row
        for row in result["adversarial_rows"]
        if int(row["pretraining_features"]["dictionary_sample_count"]) >= MIN_POSITIVE_SAMPLE_COUNT
    ]
    positive_rows = [
        row
        for row in training_rows
        if bool(row["measurement"]["exact_archive_bytes_and_sha"])
        and bool(row["measurement"]["canonical_product_tree_equal"])
        and float(row["measurement"]["saved_s"]) >= MIN_POSITIVE_SAVED_S
    ]
    positive_labels = {row["label"] for row in positive_rows}
    generalized_training_solutions = [
        solution
        for solution in result["generalized_solutions"]
        if positive_labels.intersection(solution["adversarial_admissions"])
    ]

    result["positive_unseen_training_rows"] = [
        {
            "label": row["label"],
            "dictionary_sample_count": int(row["pretraining_features"]["dictionary_sample_count"]),
            "dictionary_sample_bytes": int(row["pretraining_features"]["dictionary_sample_bytes"]),
            "exact_archive_bytes_and_sha": bool(row["measurement"]["exact_archive_bytes_and_sha"]),
            "canonical_product_tree_equal": bool(row["measurement"]["canonical_product_tree_equal"]),
            "saved_s": float(row["measurement"]["saved_s"]),
            "saved_ratio": float(row["measurement"]["saved_ratio"]),
        }
        for row in training_rows
    ]
    result["generalized_training_solutions"] = generalized_training_solutions

    summary = dict(result["summary"])
    summary.update(
        {
            "adversarial_complete": len(result["adversarial_rows"]) == 7 + ADDITIONAL_CASES,
            "positive_training_surface_rows": len(training_rows),
            "positive_unseen_exact_speedup_rows": len(positive_rows),
            "positive_training_surface_exercised": bool(training_rows),
            "generalized_training_solution_count": len(generalized_training_solutions),
            "best_generalized_training_solution": (
                generalized_training_solutions[0] if generalized_training_solutions else None
            ),
            "promotion_signal": bool(generalized_training_solutions and positive_rows),
        }
    )
    result["summary"] = summary
    result["promotion_signal"] = bool(summary["promotion_signal"])
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only positive-unseen extension of the r24 dictionary-training skip campaign. "
        "All seven v1 adversarial cases remain present; two independent large-text entropy families "
        "must exercise the real release dictionary sampler. Promotion evidence requires an admitted "
        "unseen row with >=32 actual training samples, byte-identical output, canonical tree equality "
        "and >=5 ms saved creation time. Production policy remains unchanged."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-dictionary-skip-adversarial-v2-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-dictionary-skip-adversarial-v2.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True), flush=True)

    if not result["summary"]["frozen_complete"] or not result["summary"]["adversarial_complete"]:
        raise SystemExit("dictionary-skip v2 campaign did not execute the complete frozen+unseen surface")
    if not result["summary"]["positive_training_surface_exercised"]:
        raise SystemExit("dictionary-skip v2 failed to exercise a positive unseen training surface")


if __name__ == "__main__":
    main()
