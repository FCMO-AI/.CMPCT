from __future__ import annotations

"""Evidence wrapper for the canonical ZIP-factor productization experiment.

The underlying v5 experiment deliberately encodes the promotion hypothesis in its
``gate.passed`` field and therefore exits non-zero when complete verified creation
fails to beat ZIP.  That is useful as historical research behavior, but it should
not make an exact, integrity-preserving negative experiment indistinguishable from
an invalid experiment.

This wrapper preserves every strict promotion leg.  It only separates:

* ``experiment_valid``: identity/integrity/profile/locality evidence is sound;
* ``promotion_signal``: the unchanged strict size+creation four-way contract won;
* ``release_credit``: always false for this pre-promotion research lane.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_zipfactor_canonical_productization as BASE


def run(work_root: Path) -> dict:
    result = BASE.run(work_root)
    gate = result["gate"]

    correctness_keys = (
        "exact_manifest_content_identity",
        "canonical_semantic_tree_exact",
        "independent_source_truth",
        "strong_verify_green",
        "binary_control_v3_selected",
        "measured_level_3_selected",
        "locality_green",
    )
    performance_keys = (
        "strictly_beats_zip_size",
        "strictly_beats_zstd19_size",
        "strictly_beats_zip_create",
        "strictly_beats_zstd19_create",
    )

    experiment_valid = all(gate[key] is True for key in correctness_keys)
    promotion_signal = experiment_valid and all(gate[key] is True for key in performance_keys)

    result["evidence_v2"] = {
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion_signal,
        "release_credit": False,
        "negative_result_valid": experiment_valid and not promotion_signal,
        "promotion_contract": (
            "strictly smaller AND strictly faster to create than both normal ZIP/Deflate "
            "and solid Zstd-19, with mandatory strong verification included"
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zipfactor-product-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zipfactor-product.json"))
    args = parser.parse_args()

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate": result["candidate"],
        "zip": result["zip"],
        "zstd": result["tar_zstd19"],
        "gate": result["gate"],
        "evidence_v2": result["evidence_v2"],
    }, indent=2), flush=True)

    if not result["evidence_v2"]["experiment_valid"]:
        raise SystemExit("canonical ZIP-factor productization experiment is invalid")


if __name__ == "__main__":
    main()
