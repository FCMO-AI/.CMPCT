from __future__ import annotations

"""Research-only grouped S_PACK control representation.

The current compact-control grammar repeats ``[S_PACK, blob, offset, length]`` in every
packed file row. When consecutive file rows are consecutive physical slices of the
same pack, the per-row blob/offset recipe is redundant. This oracle factors each such
run into one descriptor ``[first_file_index, blob, first_offset, lengths...]`` and
replaces the participating row storage recipes with a null placeholder. Before any
byte result is accepted, the descriptor map reconstructs the ordinary compact grammar
and that grammar must expand exactly to the shipping r24 semantic index.

No physical payload, pack boundary, locality rule, recovery rule, selector, benchmark
identity, or release threshold changes. The representation is research-only and keeps
both authenticated control copies. It is compared against the already-audited compact
control tournament and grants no release/native/Android credit.
"""

import argparse
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_r24_compact_control_oracle as CC
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from benchmarks import v030_r24_pack_run_control_oracle as RUN
from cmpct import codec as R24

LEVELS = CC.LEVELS
TARGET_SUFFIX = "07_incompressible_and_encrypted_like"


def _group_rows(base: dict, index: dict) -> tuple[list, list, int]:
    rows = [list(row) for row in base["f"]]
    source_rows = index["files"]
    if len(rows) != len(source_rows):
        raise RuntimeError("compact/source row count mismatch")

    groups: list[list] = []
    current: list | None = None
    packed_rows = 0
    for file_index, (row, source_row) in enumerate(zip(rows, source_rows, strict=True)):
        storage = row[3] if len(row) >= 6 else None
        if not (isinstance(storage, list) and len(storage) >= 4 and int(storage[0]) == int(R24.S_PACK)):
            current = None
            continue
        blob, offset, length = int(storage[1]), int(storage[2]), int(storage[3])
        if int(source_row[4]) != length or row[4] is not None:
            current = None
            continue
        if current is None or int(current[1]) != blob or int(current[2]) + sum(int(x) for x in current[3]) != offset:
            current = [file_index, blob, offset, []]
            groups.append(current)
        current[3].append(length)
        row[3] = None
        packed_rows += 1
    return rows, groups, packed_rows


def _restore_rows(rows: list, groups: list) -> list:
    out = [list(row) for row in rows]
    claimed: set[int] = set()
    for group in groups:
        if not (isinstance(group, list) and len(group) == 4):
            raise RuntimeError("invalid pack group descriptor")
        first, blob, offset, lengths = int(group[0]), int(group[1]), int(group[2]), list(group[3])
        if first < 0 or offset < 0 or not lengths:
            raise RuntimeError("invalid pack group bounds")
        cursor = offset
        for delta, raw_length in enumerate(lengths):
            idx = first + delta
            length = int(raw_length)
            if idx < 0 or idx >= len(out) or idx in claimed or length < 0:
                raise RuntimeError("invalid pack group membership")
            row = out[idx]
            if len(row) < 6 or row[3] is not None:
                raise RuntimeError("pack group does not address an encoded S_PACK placeholder")
            row[3] = [int(R24.S_PACK), blob, cursor, length]
            cursor += length
            claimed.add(idx)
    for row in out:
        if len(row) >= 6 and row[3] is None:
            raise RuntimeError("unrestored grouped S_PACK placeholder")
    return out


def _compressed_size(payload: bytes) -> tuple[int, int]:
    candidates = [(len(R24.zc(payload, level)), level) for level in LEVELS]
    return min(candidates, key=lambda item: (item[0], item[1]))


def _once(archive: Path) -> dict:
    index, physical = CC._read_index(archive)
    base = CC._compact_index(index)
    grouped_rows, groups, packed_rows = _group_rows(base, index)

    candidate = {key: value for key, value in base.items() if key != "f"}
    candidate["fg"] = grouped_rows
    candidate["pg"] = groups
    payload = msgpack.packb(candidate, use_bin_type=True)
    grouped_bytes, grouped_level = _compressed_size(payload)

    restored = dict(candidate)
    restored["f"] = _restore_rows(restored.pop("fg"), restored.pop("pg"))
    expanded = CC._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("grouped S_PACK control does not expand exactly to shipping r24 index")

    existing = RUN._pack_run_once(archive)
    baseline_bytes = int(existing["selected_compact_bytes_per_copy"])
    selected_bytes, selected_kind = min(
        ((baseline_bytes, "existing_best"), (grouped_bytes, "pack_groups")),
        key=lambda item: (item[0], item[1]),
    )
    projected = int(physical["archive_bytes"]) - 2 * int(physical["index_comp_bytes_per_copy"]) + 2 * selected_bytes
    return {
        **physical,
        "existing_best_compact_bytes_per_copy": baseline_bytes,
        "pack_group_compact_bytes_per_copy": grouped_bytes,
        "pack_group_level": grouped_level,
        "selected_kind": selected_kind,
        "selected_compact_bytes_per_copy": selected_bytes,
        "projected_archive_bytes": projected,
        "saving_vs_shipping_bytes": int(physical["archive_bytes"]) - projected,
        "incremental_saving_vs_existing_best_bytes": 2 * max(0, baseline_bytes - selected_bytes),
        "pack_groups": len(groups),
        "packed_rows": packed_rows,
        "semantic_index_roundtrip_exact": True,
        "two_authenticated_control_copies_retained": True,
        "physical_payload_records_unchanged": True,
    }


def _split_workload(label: str) -> tuple[str, str]:
    parts = str(label).split("/", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("frozen", parts[0])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    # The canonical corpus builder was renamed from the provisional _build_all_sources helper.
    # Reuse the same exact 15-workload owner as the already-green pack-run proof instead of
    # carrying a second stale corpus API.
    roots = CORPUS._build_all(work_root / "corpora")
    if len(roots) != 15:
        raise RuntimeError(f"expected exact 15-workload corpus, got {len(roots)}")
    rows = []
    for workload in sorted(roots):
        suite, name = _split_workload(workload)
        source = roots[workload]
        archive = work_root / "archives" / f"{suite}-{name}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        CC._verified_r24(source, archive)
        measured = _once(archive)
        rows.append({"suite": suite, "name": name, "workload": workload, **measured})

    target = next(row for row in rows if row["name"].endswith(TARGET_SUFFIX))
    regressions = [
        row["workload"]
        for row in rows
        if int(row["projected_archive_bytes"]) > int(row["archive_bytes"])
    ]
    exact = all(bool(row["semantic_index_roundtrip_exact"]) for row in rows)
    return {
        "schema": "cmpct-v030-r24-pack-group-control-v1",
        "contract": {
            "workloads": 15,
            "release_credit": False,
            "production_selector_change": False,
            "format_revision_change": False,
            "physical_pack_boundaries_changed": False,
            "locality_rule_changed": False,
            "recovery_rule_changed": False,
            "two_authenticated_control_copies_retained": True,
            "benchmark_identity_not_policy_input": True,
        },
        "rows": rows,
        "target": target,
        "summary": {
            "regressions": regressions,
            "target_incremental_saving_bytes": int(target["incremental_saving_vs_existing_best_bytes"]),
            "target_projected_archive_bytes": int(target["projected_archive_bytes"]),
            "target_pack_groups": int(target["pack_groups"]),
            "target_packed_rows": int(target["packed_rows"]),
        },
        "gate": {
            "experiment_valid": exact,
            "zero_projected_byte_regressions": not regressions,
            "promotion_signal": bool(exact and not regressions and int(target["incremental_saving_vs_existing_best_bytes"]) > 0),
            "passed": exact,
        },
        "claim_boundary": "Research-only grouped control map; exact semantic roundtrip is necessary but not sufficient for productization.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-pack-group-control-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-pack-group-control.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("grouped S_PACK experiment failed exact semantic roundtrip")


if __name__ == "__main__":
    main()
