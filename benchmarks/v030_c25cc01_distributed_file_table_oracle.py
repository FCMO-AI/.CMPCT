from __future__ import annotations

"""Research-only byte-feasibility oracle for distributed C25 file semantics.

Exact semantic-root ablation identified compact field ``f`` (per-file semantics/storage) as the dominant mirrored
control cost on encrypted-like. The existing physical span is already proven unable to beat Zstd-19 even with
zero-byte control, so this experiment does *not* claim that moving ``f`` alone is a solution. Instead it prices the
next ownership boundary honestly: S_PACK file rows move out of the two mirrored global roots and into one
locality-scoped table per referenced pack. Each local table keeps the file ordinal needed to reconstruct exact row
order while its pack id is implicit in table placement. The mirrored roots retain authenticated descriptors for all
local tables. Non-S_PACK rows remain global.

The emitted representation is a projection, not a readable archive grammar. Local table payload bytes, per-table
magic/length/SHA-256 framing, and two authenticated global roots are all charged. Exact reconstruction of the
original compact ``f`` rows is proved before any byte conclusion is reported. The result answers whether distributed
file-semantic ownership removes enough duplicated control to justify combining it with a genuinely smaller physical
record grammar. It grants zero product, selector, locality, recovery, or release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"
LOCAL_TABLE_MAGIC_BYTES = 4
LOCAL_TABLE_LENGTH_BYTES = 4
LOCAL_TABLE_SHA256_BYTES = 32
LOCAL_TABLE_FRAME_BYTES = LOCAL_TABLE_MAGIC_BYTES + LOCAL_TABLE_LENGTH_BYTES + LOCAL_TABLE_SHA256_BYTES


def _compress(value) -> tuple[bytes, int, int]:
    raw = msgpack.packb(value, use_bin_type=True)
    level, comp = PROFILE._compress_control(raw)
    return comp, len(raw), int(level)


def _split_file_rows(compact: dict) -> tuple[list, dict[int, list]]:
    residual = []
    groups: dict[int, list] = {}
    for file_index, row in enumerate(compact["f"]):
        storage = row[3] if len(row) > 3 else None
        if storage and int(storage[0]) == R24.S_PACK:
            pack_index = int(storage[1])
            # Pack id is implicit in the table descriptor/placement. Preserve every other semantic byte needed to
            # reconstruct the exact compact row, including kind/mode/mtime, offset, logical span and any optional
            # trailing fields. Do not infer benchmark-specific facts.
            local_storage = [int(storage[0]), int(storage[2]), int(storage[3]), *storage[4:]]
            local_row = [file_index, list(row[:3]), local_storage, *row[4:]]
            groups.setdefault(pack_index, []).append(local_row)
        else:
            residual.append([file_index, row])
    return residual, groups


def _restore_file_rows(count: int, residual: list, groups: dict[int, list]) -> list:
    restored = [None] * count
    for file_index, row in residual:
        restored[int(file_index)] = row
    for pack_index, rows in groups.items():
        for encoded in rows:
            file_index = int(encoded[0])
            prefix = list(encoded[1])
            local_storage = list(encoded[2])
            storage = [int(local_storage[0]), int(pack_index), *local_storage[1:]]
            restored[file_index] = [*prefix, storage, *encoded[3:]]
    if any(row is None for row in restored):
        raise RuntimeError("distributed file table did not reconstruct every compact file row")
    return restored


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)

    candidate = work_root / "cmpct" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, candidate, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError("locality-safe strategy unexpectedly ineligible")

    index, _data, physical = PROFILE._source_r24_parts(candidate)
    compact = CONTROL._compact_index(index)
    expanded = CONTROL._expand_index(compact, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("baseline compact semantic root does not roundtrip exactly")

    residual, groups = _split_file_rows(compact)
    restored_f = _restore_file_rows(len(compact["f"]), residual, groups)
    if restored_f != compact["f"]:
        raise RuntimeError("distributed file-semantic projection is not exact")

    local_payloads = []
    descriptors = []
    for pack_index in sorted(groups):
        comp, raw_bytes, level = _compress(groups[pack_index])
        digest = hashlib.sha256(comp).digest()
        descriptors.append([pack_index, len(comp), digest])
        local_payloads.append({
            "pack_index": pack_index,
            "rows": len(groups[pack_index]),
            "raw_bytes": raw_bytes,
            "compressed_bytes": len(comp),
            "compression_level": level,
            "framing_bytes": LOCAL_TABLE_FRAME_BYTES,
            "physical_bytes": len(comp) + LOCAL_TABLE_FRAME_BYTES,
        })

    projected_root = dict(compact)
    projected_root["f"] = residual
    # Research-only extension key. Each mirrored copy authenticates the local-table pack id, compressed length and
    # full SHA-256. The local semantic table itself exists physically only once.
    projected_root["q"] = descriptors
    root_envelope = {"x": list(index["features"]), "c": projected_root}
    root_comp, root_raw_bytes, root_level = _compress(root_envelope)

    physical_data_bytes = int(physical["data_bytes"])
    fixed_framing_bytes = int(R24.HDR.size + R24.FTR.size)
    local_tables_bytes = sum(int(x["physical_bytes"]) for x in local_payloads)
    projected_bytes = physical_data_bytes + fixed_framing_bytes + local_tables_bytes + 2 * len(root_comp)

    baseline_raw = msgpack.packb({"x": list(index["features"]), "c": compact}, use_bin_type=True)
    baseline_level, baseline_comp = PROFILE._compress_control(baseline_raw)
    baseline_projected = physical_data_bytes + fixed_framing_bytes + 2 * len(baseline_comp)
    if baseline_projected != int(row["wrapped_bytes"]):
        raise RuntimeError(
            f"baseline accounting drift: projected={baseline_projected} measured={row['wrapped_bytes']}"
        )

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])
    required_physical_shrink = max(0, projected_bytes - (zstd_bytes - 1))

    return {
        "schema": "cmpct-v030-c25cc01-distributed-file-table-oracle-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "tree_sha256": row["tree_sha256"],
        "locality": row["locality"],
        "exact_compact_file_row_reconstruction": restored_f == compact["f"],
        "baseline": {
            "wrapped_bytes": int(row["wrapped_bytes"]),
            "projected_bytes": baseline_projected,
            "control_raw_bytes": len(baseline_raw),
            "control_bytes_per_copy": len(baseline_comp),
            "control_level": int(baseline_level),
            "physical_data_bytes": physical_data_bytes,
            "fixed_header_footer_bytes": fixed_framing_bytes,
        },
        "distributed": {
            "pack_tables": len(local_payloads),
            "moved_pack_rows": sum(int(x["rows"]) for x in local_payloads),
            "residual_global_rows": len(residual),
            "local_tables": local_payloads,
            "local_tables_total_physical_bytes": local_tables_bytes,
            "mirrored_root_raw_bytes_per_copy": root_raw_bytes,
            "mirrored_root_bytes_per_copy": len(root_comp),
            "mirrored_root_level": root_level,
            "projected_total_bytes": projected_bytes,
            "bytes_saved_vs_current_wrapped": int(row["wrapped_bytes"]) - projected_bytes,
        },
        "zstd19_bytes": zstd_bytes,
        "projected_margin_below_zstd19_bytes": zstd_bytes - projected_bytes,
        "required_additional_physical_shrink_for_strict_zstd_win_bytes": required_physical_shrink,
        "gate": {
            "exact_baseline_accounting": baseline_projected == int(row["wrapped_bytes"]),
            "exact_file_semantic_reconstruction": restored_f == compact["f"],
            "current_locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "distributed_projection_beats_zstd19": projected_bytes < zstd_bytes,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Byte-feasibility projection only. The projection charges one framed/authenticated local semantic table "
            "per S_PACK plus two authenticated global roots and proves exact compact-file-row reconstruction. It does "
            "not define a reader grammar or prove locality/recovery for the projected layout, and grants no product, "
            "selector or release credit. A remaining positive byte deficit is the minimum physical-layout shrink the "
            "next grammar must additionally deliver."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-distributed-file-table-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-distributed-file-table.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("distributed-file-table oracle invalid")


if __name__ == "__main__":
    main()
