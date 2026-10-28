from __future__ import annotations

"""Evidence-validity wrapper for the C25EG01 all-15 admission campaign.

The underlying v2 experiment deliberately asks whether the original C25EG01
measured admission envelope is safe enough for promotion. It can therefore
return a technically valid negative result: all 15 candidates execute, locality
rejections fail closed, and the admitted rows are measured honestly, while one
or more admitted rows fail the immutable accepted-v0.29 floor.

A falsified selector hypothesis is useful evidence, not a broken CI harness.
This wrapper preserves every v2 measurement and threshold, separates
``experiment_valid`` from ``promotion_earned``, and exits non-zero only when the
experiment itself is incomplete/invalid. It cannot authorize selector, native,
Android, or release promotion; the ordinary release authorities remain
decisive.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_generalization_admission as V2

SCHEMA = "cmpct-v030-federated-eg01-generalization-admission-v3"


def run(work_root: Path) -> dict:
    result = V2.run(work_root)
    rows = list(result["rows"])
    admitted = [row for row in rows if row.get("admitted")]
    rejected = [row for row in rows if row.get("candidate_rejected")]
    errors = [row for row in rows if row.get("candidate_error")]

    experiment_valid = bool(
        len(rows) == 15
        and len(admitted) >= 2
        and not errors
        and all(not row.get("admitted") for row in rejected)
        and all(row.get("candidate_rejected") == "locality/decode-bound" for row in rejected)
        and result["gate"].get("dedicated_candidate_identity") is True
    )
    promotion_earned = bool(
        experiment_valid
        and admitted
        and all(row["external"]["strict"]["passed"] for row in admitted)
        and all(row["admission"]["within_release_locality_bounds"] is True for row in admitted)
        and all(float(row["admission"]["max_member_read_amplification"]) <= 8.0 for row in admitted)
        and all(int(row["admission"]["max_decode_unit_bytes"]) <= 8 * 1024 * 1024 for row in admitted)
    )

    failed_admissions = []
    for row in admitted:
        strict = row["external"]["strict"]
        if not strict["passed"]:
            failed_admissions.append(
                {
                    "label": row["label"],
                    "failed_strict_facts": sorted(key for key, value in strict.items() if key != "passed" and not value),
                    "candidate_bytes": int(row["external"]["candidate_bytes"]),
                    "accepted_v029_loss": not bool(strict["beats_accepted_v029_size"]),
                }
            )

    result = dict(result)
    result["schema"] = SCHEMA
    result["predecessor_schema"] = "cmpct-v030-federated-eg01-generalization-admission-v2"
    result["evidence_interpretation"] = {
        "experiment_valid": experiment_valid,
        "promotion_earned": promotion_earned,
        "negative_evidence_is_valid": bool(experiment_valid and not promotion_earned),
        "failed_admissions": failed_admissions,
        "release_credit": False,
        "meaning": (
            "promotion_earned=true only when every measured admission satisfies the unchanged accepted-v0.29, ZIP, "
            "Zstd-19, creation-time, locality and decode-unit contract; promotion_earned=false is preserved negative "
            "selector evidence and does not weaken ordinary release authority"
        ),
    }
    result["gate"] = {
        **dict(result["gate"]),
        "experiment_valid": experiment_valid,
        "promotion_earned": promotion_earned,
        "passed": experiment_valid,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": result["summary"],
                "evidence_interpretation": result["evidence_interpretation"],
                "gate": result["gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("federated C25EG01 all-15 experiment invalid/incomplete")


if __name__ == "__main__":
    main()
