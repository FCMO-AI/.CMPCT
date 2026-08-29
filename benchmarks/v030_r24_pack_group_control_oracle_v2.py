from __future__ import annotations

"""Research-only delta/run S_PACK control representation.

The grouped S_PACK v1 oracle proved that consecutive file rows can share one pack
recipe, but its group table still repeats absolute file indexes, absolute pack blob
indexes, and an explicit first offset. This v2 asks whether those coordinates can be
made implicit/delta-coded without changing shipping r24 semantic or physical bytes.

Each group is encoded relative to the previous group end and previous pack blob. A
zero first offset uses the short form [file_gap, blob_delta, lengths]; non-zero offsets
retain an explicit fourth field. The decoder reconstructs v1 groups and every ordinary
compact-control row, then must expand exactly to the shipping r24 index before any
projected saving is counted.
"""

import argparse
import json
from pathlib import Path
import shutil
import msgpack

from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from benchmarks import v030_r24_compact_control_oracle as CC
from benchmarks import v030_r24_pack_group_control_oracle as GROUP

LEVELS = CC.LEVELS
TARGET_SUFFIX = "07_incompressible_and_encrypted_like"


def _delta_groups(groups: list[list]) -> tuple[list[list], dict]:
    encoded = []
    previous_end = 0
    previous_blob = 0
    zero_offsets = 0
    negative_blob_deltas = 0
    for group in groups:
        if not isinstance(group, list) or len(group) != 4:
            raise RuntimeError("invalid v1 pack group")
        first, blob, offset, lengths = int(group[0]), int(group[1]), int(group[2]), list(group[3])
        if first < previous_end or blob < 0 or offset < 0 or not lengths:
            raise RuntimeError("pack groups are not monotonically file-addressable")
        gap = first - previous_end
        blob_delta = blob - previous_blob
        if blob_delta < 0:
            negative_blob_deltas += 1
        if offset == 0:
            encoded.append([gap, blob_delta, lengths])
            zero_offsets += 1
        else:
            encoded.append([gap, blob_delta, offset, lengths])
        previous_end = first + len(lengths)
        previous_blob = blob
    return encoded, {"groups": len(groups), "zero_first_offsets": zero_offsets, "negative_blob_deltas": negative_blob_deltas}


def _restore_groups(encoded: list[list]) -> list[list]:
    groups = []
    previous_end = 0
    previous_blob = 0
    for desc in encoded:
        if not isinstance(desc, list) or len(desc) not in (3, 4):
            raise RuntimeError("invalid delta pack group")
        gap = int(desc[0])
        blob_delta = int(desc[1])
        if len(desc) == 3:
            offset, lengths = 0, list(desc[2])
        else:
            offset, lengths = int(desc[2]), list(desc[3])
        first = previous_end + gap
        blob = previous_blob + blob_delta
        if gap < 0 or first < 0 or blob < 0 or offset < 0 or not lengths:
            raise RuntimeError("invalid reconstructed pack-group coordinate")
        groups.append([first, blob, offset, lengths])
        previous_end = first + len(lengths)
        previous_blob = blob
    return groups


def _compressed_size(payload: bytes) -> tuple[int, int]:
    candidates = [(len(CC.R24.zc(payload, level)), level) for level in LEVELS]
    return min(candidates, key=lambda item: (item[0], item[1]))


def _once(archive: Path) -> dict:
    index, physical = CC._read_index(archive)
    base = CC._compact_index(index)
    grouped_rows, groups, packed_rows = GROUP._group_rows(base, index)
    delta_groups, shape = _delta_groups(groups)
    if _restore_groups(delta_groups) != groups:
        raise RuntimeError("delta group table does not reconstruct grouped v1 coordinates exactly")

    candidate = {key: value for key, value in base.items() if key != "f"}
    candidate["fg"] = grouped_rows
    candidate["pg2"] = delta_groups
    payload = msgpack.packb(candidate, use_bin_type=True)
    delta_bytes, delta_level = _compressed_size(payload)

    restored = dict(candidate)
    restored_groups = _restore_groups(restored.pop("pg2"))
    restored["f"] = GROUP._restore_rows(restored.pop("fg"), restored_groups)
    expanded = CC._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("delta grouped S_PACK control does not expand exactly to shipping r24 index")

    predecessor = GROUP._once(archive)
    baseline_bytes = int(predecessor["selected_compact_bytes_per_copy"])
    selected_bytes, selected_kind = min(((baseline_bytes, "existing_best"), (delta_bytes, "delta_pack_groups_v2")), key=lambda item: (item[0], item[1]))
    projected = int(physical["archive_bytes"]) - 2 * int(physical["index_comp_bytes_per_copy"]) + 2 * selected_bytes
    return {
        **physical,
        "existing_best_compact_bytes_per_copy": baseline_bytes,
        "delta_group_raw_bytes": len(payload),
        "delta_group_compact_bytes_per_copy": delta_bytes,
        "delta_group_level": delta_level,
        "selected_kind": selected_kind,
        "selected_compact_bytes_per_copy": selected_bytes,
        "projected_archive_bytes": projected,
        "saving_vs_shipping_bytes": int(physical["archive_bytes"]) - projected,
        "incremental_saving_vs_existing_best_bytes": 2 * max(0, baseline_bytes - selected_bytes),
        "pack_groups": len(groups),
        "packed_rows": packed_rows,
        "zero_first_offsets": int(shape["zero_first_offsets"]),
        "negative_blob_deltas": int(shape["negative_blob_deltas"]),
        "semantic_index_roundtrip_exact": True,
        "v1_group_coordinates_roundtrip_exact": True,
        "two_authenticated_control_copies_retained": True,
        "physical_payload_records_unchanged": True,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = CORPUS._build_all_sources(work_root / "corpora")
    rows = []
    for suite, name in CORPUS.TARGETS:
        source = roots[(suite, name)]
        archive = work_root / "archives" / f"{suite}-{name}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        CC._verified_r24(source, archive)
        rows.append({"suite": suite, "name": name, **_once(archive)})
    target = next(row for row in rows if row["name"].endswith(TARGET_SUFFIX))
    regressions = [f"{row['suite']}/{row['name']}" for row in rows if int(row["projected_archive_bytes"]) > int(row["archive_bytes"])]
    exact = all(bool(row["semantic_index_roundtrip_exact"] and row["v1_group_coordinates_roundtrip_exact"]) for row in rows)
    return {
        "schema": "cmpct-v030-r24-pack-group-control-v2",
        "contract": {
            "workloads": len(CORPUS.TARGETS),
            "release_credit": False,
            "production_selector_change": False,
            "format_revision_change": False,
            "physical_pack_boundaries_changed": False,
            "locality_rule_changed": False,
            "recovery_rule_changed": False,
            "two_authenticated_control_copies_retained": True,
            "benchmark_identity_not_policy_input": True,
            "coordinate_law": "previous-group-end + previous-blob delta; zero first offset uses short form",
        },
        "rows": rows,
        "target": target,
        "summary": {
            "regressions": regressions,
            "target_incremental_saving_bytes": int(target["incremental_saving_vs_existing_best_bytes"]),
            "target_projected_archive_bytes": int(target["projected_archive_bytes"]),
            "target_delta_group_compact_bytes_per_copy": int(target["delta_group_compact_bytes_per_copy"]),
            "target_zero_first_offsets": int(target["zero_first_offsets"]),
            "target_pack_groups": int(target["pack_groups"]),
        },
        "gate": {
            "experiment_valid": bool(exact),
            "zero_projected_byte_regressions": not regressions,
            "promotion_signal": bool(exact and not regressions and int(target["incremental_saving_vs_existing_best_bytes"]) > 0),
            "passed": bool(exact),
        },
        "claim_boundary": "Research-only delta/run control map; exact all-15 semantic roundtrip is necessary but not sufficient for productization.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-pack-group-control-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-pack-group-control-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("delta grouped S_PACK experiment failed exact semantic roundtrip")


if __name__ == "__main__":
    main()
