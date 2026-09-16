from __future__ import annotations

"""Selective-effort frontier for C25EG05 embedded filesystem control.

C25EG04's measured office all-best floor is 5,954,155 B, 129 B above the immutable accepted-v0.29 row.
C25EG05 removes the separate filesystem-control physical pack and instead authenticates the same bounded control
bytes inside EntropyGraph's existing duplicated primary/tail metadata.  This oracle reuses the audited per-pack
compression frontier unchanged and adds only the archive-finalization hook required by that framing change.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v4 as V4
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05

EXPECTED_OFFICE_V029 = 5_954_026
EXPECTED_EG04_ALL_BEST = 5_954_155


def _prepare(source: Path, parent: Path):
    profile = parent / "profile"
    fs = EG05._prepare_profile(source, profile)
    return profile, fs


def run(work_root: Path) -> dict:
    old_candidate = V1.CAND
    old_prepare = V1._prepare
    old_build = V1.V25.build

    def finalized_build():
        stats = old_build()
        EG05.finalize_research_archive(Path(V1.V25.OUT), Path(V1.V25.ROOT))
        return stats

    V1.CAND = EG05
    V1._prepare = _prepare
    V1.V25.build = finalized_build
    try:
        result = dict(V4.run(work_root))
    finally:
        V1.V25.build = old_build
        V1._prepare = old_prepare
        V1.CAND = old_candidate
        EG05._PENDING_CONTROL.clear()

    office = next(row for row in result["rows"] if row["label"] == "neutral_hostile_v1/02_office_workspace")
    if int(office["accepted_v029_bytes"]) != EXPECTED_OFFICE_V029:
        raise RuntimeError("C25EG05 evidence drifted from immutable office v0.29 identity")
    all_best = int(office["compression_effort_upper_bound"]["all_best_archive_floor_bytes"])
    result["schema"] = "cmpct-v030-federated-eg05-embedded-fs-effort-v1"
    result["candidate_identity"] = {
        "magic_ascii": EG05.MAGIC.decode("ascii", errors="strict").rstrip("\x00"),
        "profile": "federated-eg05-embedded-fs",
        "filesystem_control": "implicit-v4 bytes embedded in authenticated primary/tail metadata",
        "separate_filesystem_pack": False,
        "patched_candidate_restored": V1.CAND is old_candidate,
        "patched_prepare_restored": V1._prepare is old_prepare,
        "patched_build_restored": V1.V25.build is old_build,
    }
    result["office_decision"] = {
        "accepted_v029_bytes": EXPECTED_OFFICE_V029,
        "predecessor_eg04_all_best_floor_bytes": EXPECTED_EG04_ALL_BEST,
        "eg05_all_best_floor_bytes": all_best,
        "saving_vs_eg04_all_best_bytes": EXPECTED_EG04_ALL_BEST - all_best,
        "strictly_beats_v029_at_all_best": all_best < EXPECTED_OFFICE_V029,
        "remaining_bytes_to_strict_v029_win": max(0, all_best - EXPECTED_OFFICE_V029 + 1),
    }
    result["claim_boundary"] = (
        "Research-only C25EG05 framing frontier. Embedding the bounded filesystem control in authenticated metadata "
        "does not authorize selector/native/Android promotion; all ordinary release authorities remain mandatory."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg05-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg05-effort.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"office_decision": result["office_decision"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("C25EG05 selective-effort measurement invalid")


if __name__ == "__main__":
    main()
