from __future__ import annotations

"""All-15 numeric-path refinement of the r24 compact-control research profile.

Current compact-control evidence is exact and zero-regression, but encrypted-like remains only a few KiB above
solid Zstd-19.  The largest metadata-heavy sources contain long sorted path runs.  This oracle asks whether a
benchmark-independent path grammar can recover more control bytes without touching payload records or either
recovery copy.

The only extra transform is generic: when two adjacent canonical paths have the same text around one final decimal
run and the same digit width, encode the integer delta from the previous path; otherwise retain the existing
prefix-length + suffix representation.  No filename, extension, workload name, path literal, hash, or benchmark
identity is an admission input.

This remains research-only.  It prices the better of the existing compact-control representation and the numeric
refinement, preserving exact expansion to the shipping r24 index.  A negative result is valid evidence and exits
successfully; promotion requires a separately bounded canonical profile with reader/recovery/native/Android parity.
"""

import argparse
import json
from pathlib import Path
import re
import shutil
import time

import msgpack

from benchmarks import v030_r24_compact_control_oracle as CC
from benchmarks import v030_r24_compact_control_composition_oracle as COMPOSE
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT

_NUMERIC = re.compile(r"^(.*?)([0-9]+)([^0-9]*)$")
LEVELS = CC.LEVELS
TARGET = COMPOSE.TARGET


def _prefix_rows_to_paths(rows: list) -> list[str]:
    out: list[str] = []
    previous = ""
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise RuntimeError("invalid compact path row")
        prefix, suffix = int(row[0]), str(row[1])
        if prefix < 0 or prefix > len(previous):
            raise RuntimeError("invalid compact path prefix")
        current = previous[:prefix] + suffix
        out.append(current)
        previous = current
    return out


def _common_prefix(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _encode_numeric_paths(paths: list[str]) -> tuple[list, int]:
    encoded = []
    previous = ""
    numeric_rows = 0
    for current in paths:
        pm = _NUMERIC.match(previous)
        cm = _NUMERIC.match(current)
        use_numeric = bool(
            pm
            and cm
            and pm.group(1) == cm.group(1)
            and pm.group(3) == cm.group(3)
            and len(pm.group(2)) == len(cm.group(2))
        )
        if use_numeric:
            delta = int(cm.group(2)) - int(pm.group(2))
            # A numeric token is only useful when it is materially smaller than restating a string suffix.
            prefix = _common_prefix(previous, current)
            literal = [0, prefix, current[prefix:]]
            token = [1, delta]
            if len(msgpack.packb(token, use_bin_type=True)) < len(msgpack.packb(literal, use_bin_type=True)):
                encoded.append(token)
                numeric_rows += 1
            else:
                encoded.append(literal)
        else:
            prefix = _common_prefix(previous, current)
            encoded.append([0, prefix, current[prefix:]])
        previous = current
    return encoded, numeric_rows


def _decode_numeric_paths(rows: list) -> list[str]:
    paths: list[str] = []
    previous = ""
    for row in rows:
        if not isinstance(row, list) or not row:
            raise RuntimeError("invalid numeric compact path row")
        tag = int(row[0])
        if tag == 0:
            if len(row) != 3:
                raise RuntimeError("invalid literal numeric compact path row")
            prefix, suffix = int(row[1]), str(row[2])
            if prefix < 0 or prefix > len(previous):
                raise RuntimeError("invalid numeric compact path prefix")
            current = previous[:prefix] + suffix
        elif tag == 1:
            if len(row) != 2:
                raise RuntimeError("invalid delta numeric compact path row")
            pm = _NUMERIC.match(previous)
            if pm is None:
                raise RuntimeError("numeric path delta lacks predecessor numeric run")
            width = len(pm.group(2))
            value = int(pm.group(2)) + int(row[1])
            if value < 0:
                raise RuntimeError("numeric path delta underflow")
            digits = str(value)
            if len(digits) > width:
                raise RuntimeError("numeric path delta exceeds fixed width")
            current = pm.group(1) + digits.zfill(width) + pm.group(3)
        else:
            raise RuntimeError("unknown numeric compact path tag")
        paths.append(current)
        previous = current
    return paths


def _paths_to_prefix_rows(paths: list[str]) -> list[list]:
    rows = []
    previous = ""
    for current in paths:
        prefix = _common_prefix(previous, current)
        rows.append([prefix, current[prefix:]])
        previous = current
    return rows


def _numeric_compact_once(archive: Path) -> dict:
    started = time.perf_counter()
    index, physical = CC._read_index(archive)
    base = CC._compact_index(index)
    paths = _prefix_rows_to_paths(base["p"])
    numeric_rows, numeric_count = _encode_numeric_paths(paths)
    candidate = {key: value for key, value in base.items() if key != "p"}
    candidate["pn"] = numeric_rows
    packed = msgpack.packb(candidate, use_bin_type=True)

    decoded_paths = _decode_numeric_paths(candidate["pn"])
    restored = dict(candidate)
    restored.pop("pn")
    restored["p"] = _paths_to_prefix_rows(decoded_paths)
    expanded = CC._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("numeric compact control does not expand exactly to shipping r24 index")

    numeric_candidates = []
    for level in LEVELS:
        compressed = R24.zc(packed, level)
        numeric_candidates.append((len(compressed), level))
    numeric_bytes, numeric_level = min(numeric_candidates, key=lambda row: (row[0], row[1]))

    base_result = CC._compact_once(archive)
    base_bytes = int(base_result["compact_index_comp_bytes_per_copy"])
    selected_numeric = numeric_bytes < base_bytes
    selected_bytes = min(base_bytes, numeric_bytes)
    projected = int(physical["archive_bytes"]) - 2 * int(physical["index_comp_bytes_per_copy"]) + 2 * selected_bytes
    return {
        **physical,
        "base_compact_bytes_per_copy": base_bytes,
        "numeric_compact_bytes_per_copy": numeric_bytes,
        "numeric_level": numeric_level,
        "numeric_rows": numeric_count,
        "path_rows": len(paths),
        "selected_numeric": selected_numeric,
        "selected_compact_bytes_per_copy": selected_bytes,
        "projected_archive_bytes": projected,
        "saving_vs_shipping_bytes": int(physical["archive_bytes"]) - projected,
        "incremental_saving_vs_base_compact_bytes": 2 * max(0, base_bytes - numeric_bytes),
        "semantic_index_roundtrip_exact": True,
        "two_authenticated_control_copies_retained": True,
        "payload_records_unchanged": True,
        "transform_s": time.perf_counter() - started,
    }


def _shipping(source: Path, archive: Path) -> tuple[dict, dict]:
    archive.parent.mkdir(parents=True, exist_ok=True)
    stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"shipping r24 verification failed: {verified!r}")
    return stats, verified


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = CORPUS._build_all(work_root / "corpus")
    rows = []
    regressions = []
    incremental_rows = []
    aggregate_shipping = 0
    aggregate_projected = 0
    aggregate_incremental = 0

    for name in sorted(roots):
        archive = work_root / "archives" / f"{name}.cmpct"
        stats, verified = _shipping(roots[name], archive)
        result = _numeric_compact_once(archive)
        row = {
            "workload": name,
            "shipping_bytes": int(result["archive_bytes"]),
            "projected_bytes": int(result["projected_archive_bytes"]),
            "saving_bytes": int(result["saving_vs_shipping_bytes"]),
            "incremental_saving_vs_base_compact_bytes": int(result["incremental_saving_vs_base_compact_bytes"]),
            "base_compact_bytes_per_copy": int(result["base_compact_bytes_per_copy"]),
            "numeric_compact_bytes_per_copy": int(result["numeric_compact_bytes_per_copy"]),
            "numeric_rows": int(result["numeric_rows"]),
            "path_rows": int(result["path_rows"]),
            "selected_numeric": bool(result["selected_numeric"]),
            "tree_sha256": verified.get("tree_sha256"),
            "dead_dictionary_elision": stats.get("r24_dead_dictionary_elision"),
            "semantic_index_roundtrip_exact": bool(result["semantic_index_roundtrip_exact"]),
            "two_control_copies": bool(result["two_authenticated_control_copies_retained"]),
            "payload_records_unchanged": bool(result["payload_records_unchanged"]),
        }
        aggregate_shipping += row["shipping_bytes"]
        aggregate_projected += row["projected_bytes"]
        aggregate_incremental += row["incremental_saving_vs_base_compact_bytes"]
        if row["projected_bytes"] > row["shipping_bytes"]:
            regressions.append(name)
        if row["incremental_saving_vs_base_compact_bytes"] > 0:
            incremental_rows.append(name)
        rows.append(row)

    target = next(row for row in rows if row["workload"] == TARGET)
    experiment_valid = bool(
        len(rows) == 15
        and not regressions
        and all(row["semantic_index_roundtrip_exact"] for row in rows)
        and all(row["two_control_copies"] for row in rows)
        and all(row["payload_records_unchanged"] for row in rows)
    )
    promotion_signal = bool(experiment_valid and aggregate_incremental > 0 and target["incremental_saving_vs_base_compact_bytes"] > 0)
    return {
        "schema": "cmpct-v030-r24-numeric-path-control-v1",
        "contract": {
            "workloads": 15,
            "policy_inputs": ["previous_canonical_path", "current_canonical_path"],
            "forbidden_policy_inputs": ["benchmark_name", "workload_label", "filename_literal", "path_literal", "content_hash"],
            "numeric_rule": "same surrounding text + same-width final decimal run -> encode integer delta when its MessagePack token is smaller; otherwise prefix+suffix",
            "two_authenticated_control_copies_retained": True,
            "physical_payload_records_unchanged": True,
            "release_credit": False,
        },
        "rows": rows,
        "summary": {
            "aggregate_shipping_bytes": aggregate_shipping,
            "aggregate_projected_bytes": aggregate_projected,
            "aggregate_saving_vs_shipping_bytes": aggregate_shipping - aggregate_projected,
            "aggregate_incremental_saving_vs_base_compact_bytes": aggregate_incremental,
            "numeric_selected_workloads": incremental_rows,
            "regressions": regressions,
            "encrypted_like_incremental_saving_bytes": target["incremental_saving_vs_base_compact_bytes"],
        },
        "gate": {
            "experiment_valid": experiment_valid,
            "zero_projected_byte_regressions": not regressions,
            "promotion_signal": promotion_signal,
            "passed": experiment_valid,
        },
        "claim_boundary": "Research-only exact control-grammar experiment. A promotion signal does not authorize a format/profile or release change.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-numeric-path-control-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-numeric-path-control.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("numeric-path compact-control experiment invalid")


if __name__ == "__main__":
    main()
