from __future__ import annotations

"""Diagnose a safer structural C25CC01 admission envelope.

The existing four-feature compact-control predicate is size-correct on the frozen target but has shown runner-sensitive
ZIP-speed counterexamples on unseen high-file-count entropy mosaics.  This oracle tests whether *physical fragmentation*
of the completed r24 candidate explains the difference.  It never consumes workload identity as a policy input.

The proposed refinement is intentionally research-only: the ordinary frozen admission remains untouched and no release
or selector credit is granted here.  A future promotion must independently generalize the refined rule before shipping.

A compact-control profile rejection is negative evidence, not a harness exception.  The diagnostic therefore records
profile-ineligible cases explicitly and keeps them outside both the current and refined admission predicates.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from benchmarks import v030_r24_compact_control_terminal_admission as ADM
from benchmarks import v030_r24_compact_control_terminal_generalization as GEN
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC

# Mechanism-level hypothesis from the exact cost-model evidence.  The frozen encrypted-like target has 57 physical
# records / 25 independently stored members; the three unstable all-packed mosaics have only 23-30 physical records
# and one non-pack member.  Requiring genuine fragmentation makes compact-control target metadata-rich r24 layouts
# instead of nearly-solid synthetic packs whose ZIP CPU margin is too small and noisy.
MIN_PHYSICAL_BLOB_RECORDS = 40
MIN_NON_PACK_MEMBERS = 8


def _candidate_structure(r24_path: Path) -> dict:
    index, _data, _physical = CC._source_r24_parts(r24_path)
    files = list(index.get("files", []))
    blobs = list(index.get("blobs", []))
    s_pack_members = 0
    non_pack_members = 0
    regular_members = 0
    for row in files:
        if len(row) < 7 or row[1] == R24.K_DIR:
            continue
        regular_members += 1
        storage = row[6]
        if storage and storage[0] == R24.S_PACK:
            s_pack_members += 1
        else:
            non_pack_members += 1
    return {
        "physical_blob_records": len(blobs),
        "regular_members": regular_members,
        "s_pack_members": s_pack_members,
        "non_pack_members": non_pack_members,
        "packed_member_fraction": s_pack_members / max(1, regular_members),
    }


def _refined_admitted(shape: dict, candidate: dict, structure: dict) -> bool:
    if not candidate.get("profile_eligible") or candidate.get("candidate_bytes") is None:
        return False
    return (
        ADM._admitted(shape, int(candidate["r24_bytes"]), int(candidate["candidate_bytes"]))
        and int(structure["physical_blob_records"]) >= MIN_PHYSICAL_BLOB_RECORDS
        and int(structure["non_pack_members"]) >= MIN_NON_PACK_MEMBERS
    )


def _measure_case(label: str, source: Path, work: Path, *, compare: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-cc-fragment-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "stage")
        shape = ADM._source_shape(stage)
        candidate = ADM._build_candidate(stage, root / "candidate")
        structure = _candidate_structure(candidate["r24"])
        eligible = bool(candidate.get("profile_eligible"))
        current = (
            eligible
            and candidate.get("candidate_bytes") is not None
            and ADM._admitted(shape, int(candidate["r24_bytes"]), int(candidate["candidate_bytes"]))
        )
        refined = _refined_admitted(shape, candidate, structure)
        candidate_bytes = candidate.get("candidate_bytes")
        row = {
            "label": label,
            **shape,
            "profile_eligible": eligible,
            "profile_reject_reason": candidate.get("profile_reject_reason"),
            "r24_bytes": int(candidate["r24_bytes"]),
            "candidate_bytes": int(candidate_bytes) if candidate_bytes is not None else None,
            "candidate_to_r24": (
                int(candidate_bytes) / max(1, int(candidate["r24_bytes"])) if candidate_bytes is not None else None
            ),
            "current_admitted": bool(current),
            "refined_admitted": bool(refined),
            "payload_unchanged": candidate.get("payload_unchanged"),
            "two_control_copies": candidate.get("two_control_copies"),
            **structure,
        }
        if compare and refined:
            competitors = ADM._competitors(stage, root / "competitors")
            row["competitors"] = competitors
            row["strict_four_way_win"] = bool(competitors["strict_four_way_win"])
        return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)

    frozen = CORPUS._build_all(args.work_root / "frozen")
    unseen = GEN._cases(args.work_root / "unseen")
    rows = []
    for name in sorted(frozen):
        rows.append(_measure_case(f"frozen/{name}", frozen[name], args.work_root, compare=True))
    for name in sorted(unseen):
        rows.append(_measure_case(f"unseen/{name}", unseen[name], args.work_root, compare=True))

    refined = [row for row in rows if row["refined_admitted"]]
    refined_counterexamples = [row["label"] for row in refined if row.get("strict_four_way_win") is not True]
    known_unstable = {
        "unseen/entropy_mosaic_640",
        "unseen/entropy_mosaic_1150",
        "unseen/entropy_mosaic_1750",
    }
    by_label = {row["label"]: row for row in rows}
    target = by_label["frozen/07_incompressible_and_encrypted_like"]
    ineligible = [row["label"] for row in rows if not row["profile_eligible"]]
    gate = {
        "exact_case_count": len(rows) == 25,
        "frozen_target_profile_eligible": target["profile_eligible"] is True,
        "frozen_target_refined_admitted": target["refined_admitted"] is True,
        "frozen_target_strict_four_way_win": target.get("strict_four_way_win") is True,
        "known_unstable_mosaics_rejected": all(by_label[name]["refined_admitted"] is False for name in known_unstable),
        "zero_refined_counterexamples": not refined_counterexamples,
        "integrity_preserved": all(
            (not row["profile_eligible"]) or (row["payload_unchanged"] is True and row["two_control_copies"] is True)
            for row in rows
        ),
        "profile_ineligibility_recorded": all(
            row["profile_eligible"] or bool(row["profile_reject_reason"])
            for row in rows
        ),
    }
    gate["diagnostic_valid"] = all(gate.values())
    result = {
        "schema": "cmpct-v030-c25cc01-fragmentation-admission-v1",
        "contract": {
            "base_predicate_inputs": ["logical_bytes", "regular_files", "r24_bytes", "candidate_bytes"],
            "additional_candidate_inputs": ["physical_blob_records", "non_pack_members"],
            "min_physical_blob_records": MIN_PHYSICAL_BLOB_RECORDS,
            "min_non_pack_members": MIN_NON_PACK_MEMBERS,
            "forbidden_inputs": ["workload_name", "path", "filename", "suffix", "content_hash", "archive_hash", "pack_hash"],
            "selector_change": False,
            "release_credit": False,
            "profile_ineligibility_is_negative_evidence": True,
            "purpose": "causal admission refinement after unseen ZIP-speed counterexamples",
        },
        "rows": rows,
        "profile_ineligible": ineligible,
        "refined_admitted": [row["label"] for row in refined],
        "refined_counterexamples": refined_counterexamples,
        "gate": gate,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "profile_ineligible": result["profile_ineligible"],
                "refined_admitted": result["refined_admitted"],
                "gate": gate,
            },
            indent=2,
        ),
        flush=True,
    )
    if not gate["diagnostic_valid"]:
        raise SystemExit("C25CC01 fragmentation admission diagnostic failed; negative evidence was preserved in artifact")


if __name__ == "__main__":
    main()
