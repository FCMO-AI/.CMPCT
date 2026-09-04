from __future__ import annotations

"""Exact office byte frontier for C25EG08 compact physical framing.

EG07's audited selective-effort evidence leaves office 42 bytes above accepted v0.29.  EG08 does not alter a
single metadata byte, physical payload byte, compression decision, reconstruction recipe or locality decision.
It removes 20 fixed redundant framing bytes plus 8 bytes from every physical-pack header by deriving values that
are already authenticated/self-described elsewhere.

Because selective effort only recompresses the existing physical packs, pack count is invariant across every
policy in the EG07 frontier.  Therefore the compact-framing delta measured from the level-1 structural graph
applies exactly to its all-best payload floor; this is arithmetic over byte-identical payloads, not an estimate.
The result is research evidence only and cannot authorize selector/native/Android promotion.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_embedded_fs_v7_effort_oracle as V7
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08

EXPECTED_OFFICE_V029 = 5_954_026
EXPECTED_EG07_FLOOR = 5_954_067


def run(work_root: Path) -> dict:
    base = V7.run(work_root / "eg07")
    office = next(row for row in base["rows"] if row["label"] == "neutral_hostile_v1/02_office_workspace")
    accepted = int(office["accepted_v029_bytes"])
    if accepted != EXPECTED_OFFICE_V029:
        raise RuntimeError("compact-framing frontier drifted from immutable office v0.29 identity")
    eg07_floor = int(office["compression_effort_upper_bound"]["all_best_archive_floor_bytes"])
    if eg07_floor != EXPECTED_EG07_FLOOR:
        raise RuntimeError(f"EG07 all-best floor drifted: {eg07_floor} != {EXPECTED_EG07_FLOOR}")
    pack_count = int(office["baseline_level1"]["physical_pack_count"])
    if pack_count <= 0 or len(office["pack_frontier"]) != pack_count:
        raise RuntimeError("compact-framing frontier cannot prove invariant physical-pack count")

    fixed_saving = (V25.HDR.size - EG08.HDR.size) + (V25.FTR.size - EG08.FTR.size)
    per_pack_saving = V25.PH.size - EG08.PH.size
    total_saving = fixed_saving + pack_count * per_pack_saving
    compact_floor = eg07_floor - total_saving
    remaining = max(0, compact_floor - accepted + 1)

    result = {
        "schema": "cmpct-v030-federated-eg08-compact-framing-frontier-v1",
        "source_evidence_schema": base["schema"],
        "candidate_identity": {
            "magic_ascii": EG08.MAGIC.decode("ascii").rstrip("\x00"),
            "profile": "federated-eg08-compact-physical-framing",
            "payload_bytes_changed": False,
            "metadata_bytes_changed": False,
            "reconstruction_graph_changed": False,
            "recovery_copy_count_changed": False,
            "integrity_digests_changed": False,
            "locality_semantics_changed": False,
        },
        "framing": {
            "inherited_header_bytes": V25.HDR.size,
            "compact_header_bytes": EG08.HDR.size,
            "inherited_pack_header_bytes": V25.PH.size,
            "compact_pack_header_bytes": EG08.PH.size,
            "inherited_footer_bytes": V25.FTR.size,
            "compact_footer_bytes": EG08.FTR.size,
            "fixed_saving_bytes": fixed_saving,
            "per_pack_saving_bytes": per_pack_saving,
        },
        "office_decision": {
            "accepted_v029_bytes": accepted,
            "eg07_all_best_floor_bytes": eg07_floor,
            "physical_pack_count": pack_count,
            "exact_compact_framing_saving_bytes": total_saving,
            "eg08_projected_all_best_floor_bytes": compact_floor,
            "strictly_beats_v029_at_same_payload_floor": compact_floor < accepted,
            "margin_below_v029_bytes": accepted - compact_floor,
            "remaining_bytes_to_strict_v029_win": remaining,
        },
        "measurement_gate": {
            "eg07_measurement_valid": bool(base["measurement_gate"]["passed"]),
            "exact_pack_count_matches_frontier": len(office["pack_frontier"]) == pack_count,
            "fixed_framing_delta_positive": fixed_saving > 0 and per_pack_saving > 0,
            "office_floor_crossed_without_payload_change": compact_floor < accepted,
        },
        "claim_boundary": (
            "Research-only structural byte proof. It proves the EG07 all-best payload floor plus C25EG08 compact "
            "framing clears the immutable office v0.29 byte floor. Shipping still requires direct candidate build, "
            "verified creation timing, hostile/recovery coverage, native/Android parity, selector admission and all "
            "ordinary v0.30 authorities."
        ),
    }
    result["measurement_gate"]["passed"] = all(result["measurement_gate"].values())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-framing-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-framing.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"office_decision": result["office_decision"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("C25EG08 compact-framing frontier failed")


if __name__ == "__main__":
    main()
