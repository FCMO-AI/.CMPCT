from __future__ import annotations

"""Research-only S_PACK run compaction for the r24 compact-control frontier.

The path-oriented compact-control experiments have now largely exhausted path text on the encrypted-like row:
numeric deltas help only slightly and suffix interning helps it by zero bytes.  The remaining compact index still
repeats complete S_PACK storage recipes for long runs of contiguous members in the same physical pack.  This oracle
asks whether those repeated pack-id/offset fields account for the last few KiB needed to cross solid Zstd-19.

The transform is deliberately narrow and benchmark-independent.  For a compact-index file row whose shipping
storage is S_PACK, whose predecessor is another S_PACK slice in the same blob, whose offset is exactly the previous
slice end, and whose logical size is otherwise derivable, the storage recipe is replaced by a continuation token.
The continuation carries only the logical length; decoder state reconstructs the exact original S_PACK recipe.
Every other row is unchanged.  Numeric path deltas may be composed because that transform is already independently
audited and exact.

This remains research-only.  It keeps both authenticated control copies, changes no physical payload record, must
expand byte-semantically to the shipping r24 index on all 15 frozen workloads, and grants no selector/native/Android
or release credit.  The target timing deliberately overcharges CMPCT with shipping r24 build + mandatory strong
verification + the extra post-build research transform.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

import msgpack

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CC
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from benchmarks import v030_r24_numeric_path_control_oracle as NUM
from benchmarks import v030_r24_suffix_path_control_oracle as SUFFIX
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT

LEVELS = CC.LEVELS
ROUNDS = 5
TARGET_SUFFIX = "07_incompressible_and_encrypted_like"
DIAGNOSTIC_SUFFIX = "08_many_tiny_files"


def _pack_run_rows(base: dict, index: dict) -> tuple[list, int]:
    compact_rows = base["f"]
    source_rows = index["files"]
    if len(compact_rows) != len(source_rows):
        raise RuntimeError("compact/source row count mismatch")

    out = []
    continuations = 0
    previous_blob: int | None = None
    previous_end: int | None = None

    for compact_row, source_row in zip(compact_rows, source_rows, strict=True):
        row = list(compact_row)
        storage = row[3] if len(row) >= 6 else None
        if isinstance(storage, list) and len(storage) >= 4 and int(storage[0]) == int(R24.S_PACK):
            blob = int(storage[1])
            offset = int(storage[2])
            length = int(storage[3])
            source_size = int(source_row[4])
            # Compact only rows for which the ordinary compact grammar already derives size from S_PACK length.
            # That makes the inverse exact: None is an unambiguous continuation token and row[4] carries length.
            if (
                previous_blob == blob
                and previous_end == offset
                and row[4] is None
                and source_size == length
            ):
                row[3] = None
                row[4] = source_size
                continuations += 1
            previous_blob = blob
            previous_end = offset + length
        else:
            previous_blob = None
            previous_end = None
        out.append(row)
    return out, continuations


def _restore_pack_run_rows(rows: list) -> list:
    out = []
    previous_blob: int | None = None
    previous_end: int | None = None
    for encoded in rows:
        row = list(encoded)
        storage = row[3] if len(row) >= 6 else None
        if len(row) >= 6 and storage is None:
            if previous_blob is None or previous_end is None:
                raise RuntimeError("pack continuation lacks predecessor S_PACK slice")
            if row[4] is None:
                raise RuntimeError("pack continuation lacks logical length")
            length = int(row[4])
            if length < 0:
                raise RuntimeError("negative pack continuation length")
            row[3] = [int(R24.S_PACK), previous_blob, previous_end, length]
            row[4] = None
            previous_end += length
        elif isinstance(storage, list) and len(storage) >= 4 and int(storage[0]) == int(R24.S_PACK):
            previous_blob = int(storage[1])
            previous_end = int(storage[2]) + int(storage[3])
        else:
            previous_blob = None
            previous_end = None
        out.append(row)
    return out


def _compressed_size(payload: bytes) -> tuple[int, int]:
    candidates = [(len(R24.zc(payload, level)), level) for level in LEVELS]
    return min(candidates, key=lambda item: (item[0], item[1]))


def _pack_run_once(archive: Path) -> dict:
    started = time.perf_counter()
    index, physical = CC._read_index(archive)
    base = CC._compact_index(index)
    run_rows, continuation_count = _pack_run_rows(base, index)

    paths = NUM._prefix_rows_to_paths(base["p"])
    numeric_rows, numeric_count = NUM._encode_numeric_paths(paths)

    # Candidate A: pack-run storage with ordinary prefix paths.
    pack_candidate = {key: value for key, value in base.items() if key != "f"}
    pack_candidate["fr"] = run_rows
    pack_payload = msgpack.packb(pack_candidate, use_bin_type=True)
    pack_bytes, pack_level = _compressed_size(pack_payload)

    # Candidate B: compose the same exact pack-run storage with the independently audited numeric path grammar.
    numeric_pack_candidate = {key: value for key, value in base.items() if key not in ("f", "p")}
    numeric_pack_candidate["fr"] = run_rows
    numeric_pack_candidate["pn"] = numeric_rows
    numeric_pack_payload = msgpack.packb(numeric_pack_candidate, use_bin_type=True)
    numeric_pack_bytes, numeric_pack_level = _compressed_size(numeric_pack_payload)

    # Reconstruct the exact ordinary compact grammar from the most transformed representation.
    restored = dict(numeric_pack_candidate)
    restored["f"] = _restore_pack_run_rows(restored.pop("fr"))
    restored["p"] = NUM._paths_to_prefix_rows(NUM._decode_numeric_paths(restored.pop("pn")))
    expanded = CC._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("pack-run compact control does not expand exactly to shipping r24 index")

    # Current best path/control evidence is the suffix/numeric/base tournament.  Pack-run only gets credit if the
    # complete compressed control plane beats that already-audited representation.
    current_best = SUFFIX._hybrid_compact_once(archive)
    baseline_bytes = int(current_best["selected_compact_bytes_per_copy"])
    selected_bytes, selected_rank, selected_kind = min(
        (
            (baseline_bytes, 0, "existing_best"),
            (pack_bytes, 1, "pack_run"),
            (numeric_pack_bytes, 2, "numeric_pack_run"),
        ),
        key=lambda item: (item[0], item[1]),
    )
    projected = int(physical["archive_bytes"]) - 2 * int(physical["index_comp_bytes_per_copy"]) + 2 * selected_bytes
    return {
        **physical,
        "existing_best_compact_bytes_per_copy": baseline_bytes,
        "pack_run_compact_bytes_per_copy": pack_bytes,
        "pack_run_level": pack_level,
        "numeric_pack_run_compact_bytes_per_copy": numeric_pack_bytes,
        "numeric_pack_run_level": numeric_pack_level,
        "selected_kind": selected_kind,
        "selected_compact_bytes_per_copy": selected_bytes,
        "projected_archive_bytes": projected,
        "saving_vs_shipping_bytes": int(physical["archive_bytes"]) - projected,
        "incremental_saving_vs_existing_best_bytes": 2 * max(0, baseline_bytes - selected_bytes),
        "pack_run_continuations": continuation_count,
        "numeric_path_rows": numeric_count,
        "semantic_index_roundtrip_exact": True,
        "two_authenticated_control_copies_retained": True,
        "physical_payload_records_unchanged": True,
        "transform_s": time.perf_counter() - started,
    }


def _shipping(source: Path, archive: Path) -> tuple[dict, dict, float]:
    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = PRODUCT.strong_verify(archive)
    verify_s = time.perf_counter() - started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"shipping r24 verification failed: {verified!r}")
    return stats, verified, build_s + verify_s


def _find_by_suffix(roots: dict[str, Path], suffix: str) -> tuple[str, Path]:
    matches = [(name, root) for name, root in roots.items() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one workload ending {suffix!r}, got {[name for name, _ in matches]!r}")
    return matches[0]


def _target_timing(source: Path, work: Path) -> dict:
    samples = []
    cmpct_sizes: set[int] = set()
    zip_sizes: set[int] = set()
    zstd_sizes: set[int] = set()
    trees: set[str] = set()
    for rep in range(ROUNDS):
        order = ["cmpct", "zip", "zstd"]
        order = order[rep % 3 :] + order[: rep % 3]
        current: dict[str, dict] = {}
        for name in order:
            if name == "cmpct":
                archive = work / f"target-{rep}.cmpct"
                _stats, verified, complete = _shipping(source, archive)
                transformed = _pack_run_once(archive)
                current[name] = {
                    **transformed,
                    "tree_sha256": verified.get("tree_sha256"),
                    # Deliberately overcharge: productization would encode this control plane directly.
                    "conservative_create_s": complete + float(transformed["transform_s"]),
                }
            elif name == "zip":
                current[name] = EXT._zip(source, work / f"target-{rep}.zip", work / f"zip-out-{rep}")
            else:
                zwork = work / f"zstd-work-{rep}"
                zwork.mkdir(parents=True, exist_ok=True)
                current[name] = EXT._tar_zstd(
                    source,
                    work / f"target-{rep}.tar.zst",
                    work / f"zstd-out-{rep}",
                    zwork,
                )
        cmpct_sizes.add(int(current["cmpct"]["projected_archive_bytes"]))
        zip_sizes.add(int(current["zip"]["archive_bytes"]))
        zstd_sizes.add(int(current["zstd"]["archive_bytes"]))
        trees.add(str(current["cmpct"]["tree_sha256"]))
        samples.append(
            {
                "cmpct_create_s": float(current["cmpct"]["conservative_create_s"]),
                "zip_create_s": float(current["zip"]["create_s"]),
                "zstd19_create_s": float(current["zstd"]["create_s"]),
            }
        )
    cmpct_bytes = next(iter(cmpct_sizes))
    zip_bytes = next(iter(zip_sizes))
    zstd_bytes = next(iter(zstd_sizes))
    cmpct_create = statistics.median(row["cmpct_create_s"] for row in samples)
    zip_create = statistics.median(row["zip_create_s"] for row in samples)
    zstd_create = statistics.median(row["zstd19_create_s"] for row in samples)
    return {
        "rounds": ROUNDS,
        "projected_bytes": cmpct_bytes,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "median_conservative_create_s": cmpct_create,
        "median_zip_create_s": zip_create,
        "median_zstd19_create_s": zstd_create,
        "size_deterministic": len(cmpct_sizes) == len(zip_sizes) == len(zstd_sizes) == 1,
        "tree_deterministic": len(trees) == 1,
        "strict_four_way_potential": (
            cmpct_bytes < zip_bytes
            and cmpct_bytes < zstd_bytes
            and cmpct_create < zip_create
            and cmpct_create < zstd_create
        ),
        "samples": samples,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = CORPUS._build_all(work_root / "corpus")
    if len(roots) != 15:
        raise RuntimeError(f"expected exact 15-workload corpus, got {len(roots)}")

    rows = []
    regressions = []
    aggregate_shipping = 0
    aggregate_projected = 0
    aggregate_incremental = 0
    for name in sorted(roots):
        archive = work_root / "archives" / f"{name}.cmpct"
        stats, verified, _complete = _shipping(roots[name], archive)
        result = _pack_run_once(archive)
        row = {
            "workload": name,
            "shipping_bytes": int(result["archive_bytes"]),
            "projected_bytes": int(result["projected_archive_bytes"]),
            "saving_bytes": int(result["saving_vs_shipping_bytes"]),
            "incremental_saving_vs_existing_best_bytes": int(result["incremental_saving_vs_existing_best_bytes"]),
            "selected_kind": result["selected_kind"],
            "pack_run_continuations": int(result["pack_run_continuations"]),
            "numeric_path_rows": int(result["numeric_path_rows"]),
            "semantic_index_roundtrip_exact": bool(result["semantic_index_roundtrip_exact"]),
            "two_control_copies": bool(result["two_authenticated_control_copies_retained"]),
            "payload_records_unchanged": bool(result["physical_payload_records_unchanged"]),
            "tree_sha256": verified.get("tree_sha256"),
            "dead_dictionary_elision": stats.get("r24_dead_dictionary_elision"),
        }
        rows.append(row)
        aggregate_shipping += row["shipping_bytes"]
        aggregate_projected += row["projected_bytes"]
        aggregate_incremental += row["incremental_saving_vs_existing_best_bytes"]
        if row["projected_bytes"] > row["shipping_bytes"]:
            regressions.append(name)

    target_name, target_root = _find_by_suffix(roots, TARGET_SUFFIX)
    diagnostic_name, _diagnostic_root = _find_by_suffix(roots, DIAGNOSTIC_SUFFIX)
    target_row = next(row for row in rows if row["workload"] == target_name)
    diagnostic_row = next(row for row in rows if row["workload"] == diagnostic_name)
    timing = _target_timing(target_root, work_root / "target-timing")
    target_row = {**target_row, **timing}

    experiment_valid = (
        len(rows) == 15
        and not regressions
        and all(row["semantic_index_roundtrip_exact"] for row in rows)
        and all(row["two_control_copies"] for row in rows)
        and all(row["payload_records_unchanged"] for row in rows)
        and timing["size_deterministic"]
        and timing["tree_deterministic"]
    )
    promotion_signal = bool(
        experiment_valid
        and target_row["incremental_saving_vs_existing_best_bytes"] > 0
        and timing["strict_four_way_potential"]
    )
    return {
        "schema": "cmpct-v030-r24-pack-run-control-v1",
        "contract": {
            "workloads": 15,
            "release_credit": False,
            "production_selector_change": False,
            "format_revision_change": False,
            "two_authenticated_control_copies_retained": True,
            "physical_payload_records_unchanged": True,
            "policy_inputs": [
                "authenticated_storage_tag",
                "authenticated_pack_blob_index",
                "authenticated_pack_offset",
                "authenticated_logical_size",
            ],
            "forbidden_policy_inputs": [
                "benchmark_name",
                "workload_label",
                "content_hash",
                "file_path_literal",
                "frozen_pack_hash",
            ],
            "target_timing_boundary": "shipping r24 build + mandatory strong verification + post-build research transform",
        },
        "summary": {
            "aggregate_shipping_bytes": aggregate_shipping,
            "aggregate_projected_bytes": aggregate_projected,
            "aggregate_saving_vs_shipping_bytes": aggregate_shipping - aggregate_projected,
            "aggregate_incremental_saving_vs_existing_best_bytes": aggregate_incremental,
            "regressions": regressions,
            "target_workload": target_name,
            "target_incremental_saving_bytes": int(target_row["incremental_saving_vs_existing_best_bytes"]),
            "target_projected_bytes": int(target_row["projected_bytes"]),
            "target_zstd19_bytes": int(target_row["zstd19_bytes"]),
            "target_pack_run_continuations": int(target_row["pack_run_continuations"]),
            "diagnostic_workload": diagnostic_name,
            "diagnostic_incremental_saving_bytes": int(diagnostic_row["incremental_saving_vs_existing_best_bytes"]),
            "diagnostic_pack_run_continuations": int(diagnostic_row["pack_run_continuations"]),
        },
        "target": target_row,
        "rows": rows,
        "gate": {
            "experiment_valid": experiment_valid,
            "zero_projected_byte_regressions": not regressions,
            "target_strict_four_way_potential": bool(timing["strict_four_way_potential"]),
            "promotion_signal": promotion_signal,
            "passed": experiment_valid,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2))
    return 0 if result["gate"]["experiment_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
