from __future__ import annotations

"""Research-only CPU-aware source prefilter for C25CC01.

This diagnostic tests whether a minimum average regular-file size can safely narrow compact-control admission.
Profile ineligibility under the release locality/decode-unit law is negative evidence: it is recorded explicitly,
never passed into the broad candidate predicate, and never earns selector or release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_terminal_admission as ADM
from benchmarks import v030_r24_compact_control_terminal_generalization as GEN

MIN_PREFILTER_FILES = 1000
MIN_AVG_REGULAR_BYTES = 6 * 1024


def _proposed_source_prefilter(shape: dict) -> bool:
    return (
        int(shape["logical_bytes"]) >= ADM.MIN_LOGICAL_BYTES
        and int(shape["regular_files"]) >= MIN_PREFILTER_FILES
        and float(shape["logical_bytes"]) / max(1, int(shape["regular_files"])) >= MIN_AVG_REGULAR_BYTES
    )


def _cases(root: Path) -> dict[str, Path]:
    cases = GEN._cases(root / "existing")
    probes = {
        "entropy_1200x5k": (12001, 1200, 5 * 1024),
        "entropy_1200x6k": (12002, 1200, 6 * 1024),
        "entropy_1200x7k": (12003, 1200, 7 * 1024),
        "entropy_1200x8k": (12004, 1200, 8 * 1024),
        "entropy_1800x5k": (18001, 1800, 5 * 1024),
        "entropy_1800x7k": (18002, 1800, 7 * 1024),
    }
    for name, (seed, files, size) in probes.items():
        dst = root / "boundary" / name
        GEN._write_entropy_tree(dst, seed=seed, files=files, size=size)
        cases[name] = dst
    return cases


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows = []
    cases = _cases(work_root / "sources")

    for name, source in cases.items():
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-c25-avg-", dir=work_root) as td_raw:
            td = Path(td_raw)
            stage = EXT._normalized_stage(source, td / "stage")
            shape = ADM._source_shape(stage)
            candidate = ADM._build_candidate(stage, td / "preflight")
            eligible = bool(candidate.get("profile_eligible"))
            candidate_bytes = candidate.get("candidate_bytes")
            broad = (
                eligible
                and candidate_bytes is not None
                and ADM._admitted(shape, int(candidate["r24_bytes"]), int(candidate_bytes))
            )
            source_prefilter = _proposed_source_prefilter(shape)
            proposed = bool(source_prefilter and broad)
            row = {
                "case": name,
                **shape,
                "average_regular_bytes": float(shape["logical_bytes"]) / max(1, int(shape["regular_files"])),
                "profile_eligible": eligible,
                "profile_reject_reason": candidate.get("profile_reject_reason"),
                "r24_bytes": int(candidate["r24_bytes"]),
                "candidate_bytes": int(candidate_bytes) if candidate_bytes is not None else None,
                "candidate_to_r24": (
                    int(candidate_bytes) / max(1, int(candidate["r24_bytes"])) if candidate_bytes is not None else None
                ),
                "broad_candidate_admitted": bool(broad),
                "proposed_source_prefilter": bool(source_prefilter),
                "proposed_shipping_admitted": proposed,
                "payload_unchanged": candidate.get("payload_unchanged"),
                "two_control_copies": candidate.get("two_control_copies"),
            }
            if proposed:
                competitors = ADM._competitors(stage, td / "competitors")
                row["competitors"] = competitors
                row["strict_four_way_win"] = bool(competitors["strict_four_way_win"])
            rows.append(row)

    admitted = [r for r in rows if r["proposed_shipping_admitted"]]
    losers = [r for r in admitted if not r.get("strict_four_way_win", False)]
    ineligible = [r for r in rows if not r["profile_eligible"]]
    counterexample_1750 = next(r for r in rows if r["case"] == "entropy_mosaic_1750")
    positive_above_boundary = [
        r for r in admitted
        if r["case"] in {"entropy_1200x7k", "entropy_1200x8k", "entropy_1800x7k"}
    ]
    rejected_below_boundary = [
        r for r in rows
        if r["case"] in {"entropy_1200x5k", "entropy_1800x5k"} and not r["proposed_shipping_admitted"]
    ]
    promotion = (
        bool(admitted)
        and not losers
        and not counterexample_1750["proposed_shipping_admitted"]
        and len(positive_above_boundary) >= 1
        and len(rejected_below_boundary) == 2
        and all(r["payload_unchanged"] is True and r["two_control_copies"] is True for r in admitted)
    )
    experiment_valid = (
        len(rows) == 16
        and all(
            (not r["profile_eligible"])
            or (r["payload_unchanged"] is True and r["two_control_copies"] is True)
            for r in rows
        )
        and all(bool(r["profile_reject_reason"]) for r in ineligible)
    )
    return {
        "schema": "cmpct-v030-c25cc01-average-size-admission-oracle-v1",
        "contract": {
            "source_inputs": ["logical_bytes", "regular_files", "average_regular_bytes"],
            "candidate_inputs": ["r24_bytes", "candidate_bytes"],
            "forbidden_inputs": ["workload_name", "path", "filename", "suffix", "content_hash", "archive_hash", "pack_hash"],
            "min_prefilter_regular_files": MIN_PREFILTER_FILES,
            "min_average_regular_bytes": MIN_AVG_REGULAR_BYTES,
            "broad_predicate_unchanged": True,
            "comparator_rounds": ADM.ROUNDS,
            "ties_fail": True,
            "selector_change": False,
            "release_credit": False,
            "profile_ineligibility_is_negative_evidence": True,
        },
        "rows": rows,
        "profile_ineligible_cases": [r["case"] for r in ineligible],
        "admitted_count": len(admitted),
        "counterexamples": [r["case"] for r in losers],
        "known_1750_rejected": not counterexample_1750["proposed_shipping_admitted"],
        "positive_above_boundary_count": len(positive_above_boundary),
        "rejected_below_boundary_count": len(rejected_below_boundary),
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion,
        "selector_change": False,
        "release_credit": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("C25CC01 average-size admission experiment invalid")


if __name__ == "__main__":
    main()
