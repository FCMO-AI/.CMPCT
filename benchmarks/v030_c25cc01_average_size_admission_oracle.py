from __future__ import annotations

"""Research-only CPU-aware source prefilter for C25CC01.

The current shipping two-stage selector is structurally sound on the frozen target but admits an unseen high-file-
count entropy mosaic whose compact-control archive is smaller than ZIP/Zstd yet a few milliseconds slower than ZIP.
The observed difference is consistent with fixed per-file/control work being insufficiently amortized when average
regular-file size becomes too small.

This oracle tests a deliberately conservative source-only refinement before any selector change: keep the existing
>=1000-file shape requirement and require >=6 KiB average regular-file size. It preserves the existing broad
candidate/r24 predicate unchanged. The suite includes the existing ten unseen/adversarial cases plus fresh flat
high-file-count entropy probes immediately below, at, and above the proposed average-size boundary. Every case that
would pass the proposed two-stage selector must strictly beat both ZIP and Zstd-19 in size and complete C25CC01
build+strong-verification time. A single admitted loser blocks promotion. No benchmark/path/hash identity is used.
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
            broad = ADM._admitted(shape, candidate["r24_bytes"], candidate["candidate_bytes"])
            source_prefilter = _proposed_source_prefilter(shape)
            proposed = bool(source_prefilter and broad)
            row = {
                "case": name,
                **shape,
                "average_regular_bytes": float(shape["logical_bytes"]) / max(1, int(shape["regular_files"])),
                "r24_bytes": int(candidate["r24_bytes"]),
                "candidate_bytes": int(candidate["candidate_bytes"]),
                "candidate_to_r24": int(candidate["candidate_bytes"]) / max(1, int(candidate["r24_bytes"])),
                "broad_candidate_admitted": bool(broad),
                "proposed_source_prefilter": bool(source_prefilter),
                "proposed_shipping_admitted": proposed,
                "payload_unchanged": bool(candidate["payload_unchanged"]),
                "two_control_copies": bool(candidate["two_control_copies"]),
            }
            if proposed:
                competitors = ADM._competitors(stage, td / "competitors")
                row["competitors"] = competitors
                row["strict_four_way_win"] = bool(competitors["strict_four_way_win"])
            rows.append(row)

    admitted = [r for r in rows if r["proposed_shipping_admitted"]]
    losers = [r for r in admitted if not r.get("strict_four_way_win", False)]
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
        and all(r["payload_unchanged"] and r["two_control_copies"] for r in admitted)
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
        },
        "rows": rows,
        "admitted_count": len(admitted),
        "counterexamples": [r["case"] for r in losers],
        "known_1750_rejected": not counterexample_1750["proposed_shipping_admitted"],
        "positive_above_boundary_count": len(positive_above_boundary),
        "rejected_below_boundary_count": len(rejected_below_boundary),
        "experiment_valid": len(rows) == 16 and all(r["payload_unchanged"] and r["two_control_copies"] for r in rows),
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
