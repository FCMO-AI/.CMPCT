from __future__ import annotations

"""Selective-effort frontier for C25EG04 default/delta filesystem control.

C25EG03's exact all-best office floor is 5,954,199 B, only 173 B above the immutable accepted-v0.29
5,954,026 B row.  C25EG04 changes no federated reconstruction mechanism or compression search: it removes
remaining authenticated filesystem-control repetition and shortens only the hidden member name inside the
already-reserved r25 namespace.  The audited selective-effort/comparator methodology is reused unchanged.

Research evidence only.  No shipping selector, native/Android dispatch, accepted baseline, or threshold changes.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v4 as V4
from experiments import entropygraph_v030_federated_implicit_candidate_v4 as EG04


EXPECTED_OFFICE_V029 = 5_954_026
EXPECTED_PREDECESSOR_ALL_BEST = 5_954_199


def _prepare(source: Path, parent: Path):
    profile = parent / "profile"
    fs = EG04._prepare_profile(source, profile)
    return profile, fs


def run(work_root: Path) -> dict:
    old_candidate = V1.CAND
    old_prepare = V1._prepare
    V1.CAND = EG04
    V1._prepare = _prepare
    try:
        result = dict(V4.run(work_root))
    finally:
        V1.CAND = old_candidate
        V1._prepare = old_prepare

    office = next(row for row in result["rows"] if row["label"] == "neutral_hostile_v1/02_office_workspace")
    if int(office["accepted_v029_bytes"]) != EXPECTED_OFFICE_V029:
        raise RuntimeError("C25EG04 evidence drifted from immutable office v0.29 identity")
    all_best = int(office["compression_effort_upper_bound"]["all_best_archive_floor_bytes"])
    result["schema"] = "cmpct-v030-federated-eg04-default-delta-effort-v1"
    result["candidate_identity"] = {
        "magic_ascii": EG04.MAGIC.decode("ascii", errors="strict").rstrip("\x00"),
        "profile": "federated-eg04-default-delta-fs",
        "internal_manifest_path": EG04.INTERNAL_MANIFEST,
        "filesystem_control": "implicit regular paths + default/delta metadata v4",
        "patched_candidate_restored": V1.CAND is old_candidate,
        "patched_prepare_restored": V1._prepare is old_prepare,
    }
    result["office_decision"] = {
        "accepted_v029_bytes": EXPECTED_OFFICE_V029,
        "predecessor_eg03_all_best_floor_bytes": EXPECTED_PREDECESSOR_ALL_BEST,
        "eg04_all_best_floor_bytes": all_best,
        "saving_vs_eg03_all_best_bytes": EXPECTED_PREDECESSOR_ALL_BEST - all_best,
        "strictly_beats_v029_at_all_best": all_best < EXPECTED_OFFICE_V029,
    }
    result["claim_boundary"] = (
        "Research-only C25EG04 framing frontier. A byte win cannot authorize selector/native/Android promotion; "
        "all normal v0.30 release authorities remain mandatory and unchanged."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg04-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg04-effort.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"office_decision": result["office_decision"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("C25EG04 selective-effort measurement invalid")


if __name__ == "__main__":
    main()
