from __future__ import annotations

"""Selective-effort frontier for C25EG07 hybrid scalar/RLE filesystem control.

Exact EG06 evidence leaves office 42 bytes short of the immutable accepted-v0.29 floor.  EG07 keeps the same
physical EntropyGraph and recovery model and changes only authenticated filesystem-control framing.  The audited
per-pack selective-effort frontier is reused unchanged so any byte delta is causal.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v4 as V4
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EXPECTED_OFFICE_V029 = 5_954_026
EXPECTED_EG06_ALL_BEST = 5_954_067


def _prepare(source: Path, parent: Path):
    profile = parent / "profile"
    fs = EG07._prepare_profile(source, profile)
    return profile, fs


def run(work_root: Path) -> dict:
    old_candidate = V1.CAND
    old_prepare = V1._prepare
    old_build = V1.V25.build

    def finalized_build():
        stats = old_build()
        EG07.finalize_research_archive(Path(V1.V25.OUT), Path(V1.V25.ROOT))
        return stats

    V1.CAND = EG07
    V1._prepare = _prepare
    V1.V25.build = finalized_build
    try:
        result = dict(V4.run(work_root))
    finally:
        V1.V25.build = old_build
        V1._prepare = old_prepare
        V1.CAND = old_candidate
        EG07._PENDING_CONTROL.clear()

    office = next(row for row in result["rows"] if row["label"] == "neutral_hostile_v1/02_office_workspace")
    if int(office["accepted_v029_bytes"]) != EXPECTED_OFFICE_V029:
        raise RuntimeError("C25EG07 evidence drifted from immutable office v0.29 identity")
    all_best = int(office["compression_effort_upper_bound"]["all_best_archive_floor_bytes"])
    result["schema"] = "cmpct-v030-federated-eg07-hybrid-rle-effort-v1"
    result["candidate_identity"] = {
        "magic_ascii": EG07.MAGIC.decode("ascii", errors="strict").rstrip("\x00"),
        "profile": "federated-eg07-hybrid-rle-fs",
        "filesystem_control": "implicit-v6 scalar-default hybrid RLE embedded in authenticated primary/tail metadata",
        "separate_filesystem_pack": False,
        "patched_candidate_restored": V1.CAND is old_candidate,
        "patched_prepare_restored": V1._prepare is old_prepare,
        "patched_build_restored": V1.V25.build is old_build,
    }
    result["office_decision"] = {
        "accepted_v029_bytes": EXPECTED_OFFICE_V029,
        "predecessor_eg06_all_best_floor_bytes": EXPECTED_EG06_ALL_BEST,
        "eg07_all_best_floor_bytes": all_best,
        "saving_vs_eg06_all_best_bytes": EXPECTED_EG06_ALL_BEST - all_best,
        "strictly_beats_v029_at_all_best": all_best < EXPECTED_OFFICE_V029,
        "remaining_bytes_to_strict_v029_win": max(0, all_best - EXPECTED_OFFICE_V029 + 1),
    }
    result["claim_boundary"] = (
        "Research-only C25EG07 framing frontier. A byte win cannot authorize selector/native/Android promotion; "
        "all ordinary v0.30 release authorities remain mandatory."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg07-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg07-effort.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"office_decision": result["office_decision"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("C25EG07 selective-effort measurement invalid")


if __name__ == "__main__":
    main()
