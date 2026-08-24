from __future__ import annotations

"""All-15 suffix-table refinement of the r24 compact-control research profile.

Prefix-delta paths are good at repeated directory prefixes but repeatedly pay terminal filename suffixes such as
`.bin`, `.json`, and `.gz`.  The numeric-path refinement separately handles same-width decimal runs.  This oracle
combines both ideas with a tiny deterministic suffix table derived only from the canonical path stream itself.

For each path, the encoder independently chooses the smallest MessagePack token among the existing literal
prefix+suffix row, the audited same-width numeric delta, and a suffix-table row.  The entire resulting control
plane must then compress smaller than the previously best base/numeric control representation before it receives
any byte credit.  The transform preserves two authenticated control copies, leaves every physical payload record
unchanged, and must expand exactly to the shipping r24 index on all 15 frozen workloads.

This is research-only.  A positive result is evidence for a bounded compact-control product profile; it grants no
release, selector, native, or Android credit by itself.
"""

import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import time

import msgpack

from benchmarks import v030_r24_compact_control_oracle as CC
from benchmarks import v030_r24_compact_control_composition_oracle as COMPOSE
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from benchmarks import v030_r24_numeric_path_control_oracle as NUM
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT

_NUMERIC = re.compile(r"^(.*?)([0-9]+)([^0-9]*)$")
LEVELS = CC.LEVELS
TARGET = COMPOSE.TARGET
MAX_SUFFIXES = 31
MIN_SUFFIX_USES = 4
MAX_SUFFIX_CHARS = 24


def _suffix_table(paths: list[str]) -> list[str]:
    counts: Counter[str] = Counter()
    for path in paths:
        suffix = PurePosixPath(path).suffix
        if 2 <= len(suffix) <= MAX_SUFFIX_CHARS:
            counts[suffix] += 1
    eligible = [suffix for suffix, count in counts.items() if count >= MIN_SUFFIX_USES]
    # Prefer suffixes with the largest raw repeated-byte opportunity, then deterministic lexical order.
    eligible.sort(key=lambda suffix: (-(len(suffix) * (counts[suffix] - 1)), suffix))
    return eligible[:MAX_SUFFIXES]


def _numeric_token(previous: str, current: str):
    pm = _NUMERIC.match(previous)
    cm = _NUMERIC.match(current)
    if not (
        pm
        and cm
        and pm.group(1) == cm.group(1)
        and pm.group(3) == cm.group(3)
        and len(pm.group(2)) == len(cm.group(2))
    ):
        return None
    delta = int(cm.group(2)) - int(pm.group(2))
    token = [1, delta]
    return token


def _encode_hybrid_paths(paths: list[str], suffixes: list[str]) -> tuple[list, int, int]:
    suffix_ids = {suffix: index for index, suffix in enumerate(suffixes)}
    rows = []
    numeric_rows = 0
    suffix_rows = 0
    previous = ""
    for current in paths:
        prefix = NUM._common_prefix(previous, current)
        tail = current[prefix:]
        choices: list[tuple[int, int, list]] = []

        literal = [0, prefix, tail]
        choices.append((len(msgpack.packb(literal, use_bin_type=True)), 0, literal))

        numeric = _numeric_token(previous, current)
        if numeric is not None:
            choices.append((len(msgpack.packb(numeric, use_bin_type=True)), 1, numeric))

        suffix = PurePosixPath(current).suffix
        if suffix in suffix_ids and tail.endswith(suffix):
            middle = tail[: -len(suffix)]
            token = [2, prefix, middle, suffix_ids[suffix]]
            choices.append((len(msgpack.packb(token, use_bin_type=True)), 2, token))

        _size, tag, selected = min(choices, key=lambda item: (item[0], item[1]))
        rows.append(selected)
        numeric_rows += int(tag == 1)
        suffix_rows += int(tag == 2)
        previous = current
    return rows, numeric_rows, suffix_rows


def _decode_hybrid_paths(rows: list, suffixes: list[str]) -> list[str]:
    paths: list[str] = []
    previous = ""
    for row in rows:
        if not isinstance(row, list) or not row:
            raise RuntimeError("invalid hybrid compact path row")
        tag = int(row[0])
        if tag == 0:
            if len(row) != 3:
                raise RuntimeError("invalid literal hybrid compact path row")
            prefix, tail = int(row[1]), str(row[2])
            if prefix < 0 or prefix > len(previous):
                raise RuntimeError("invalid hybrid compact path prefix")
            current = previous[:prefix] + tail
        elif tag == 1:
            if len(row) != 2:
                raise RuntimeError("invalid numeric hybrid compact path row")
            pm = _NUMERIC.match(previous)
            if pm is None:
                raise RuntimeError("numeric hybrid path delta lacks predecessor numeric run")
            width = len(pm.group(2))
            value = int(pm.group(2)) + int(row[1])
            if value < 0:
                raise RuntimeError("numeric hybrid path delta underflow")
            digits = str(value)
            if len(digits) > width:
                raise RuntimeError("numeric hybrid path delta exceeds fixed width")
            current = pm.group(1) + digits.zfill(width) + pm.group(3)
        elif tag == 2:
            if len(row) != 4:
                raise RuntimeError("invalid suffix-table hybrid compact path row")
            prefix, middle, suffix_id = int(row[1]), str(row[2]), int(row[3])
            if prefix < 0 or prefix > len(previous):
                raise RuntimeError("invalid suffix-table hybrid compact path prefix")
            if suffix_id < 0 or suffix_id >= len(suffixes):
                raise RuntimeError("invalid suffix-table id")
            current = previous[:prefix] + middle + suffixes[suffix_id]
        else:
            raise RuntimeError("unknown hybrid compact path tag")
        paths.append(current)
        previous = current
    return paths


def _compressed_size(payload: bytes) -> tuple[int, int]:
    candidates = [(len(R24.zc(payload, level)), level) for level in LEVELS]
    return min(candidates, key=lambda item: (item[0], item[1]))


def _hybrid_compact_once(archive: Path) -> dict:
    started = time.perf_counter()
    index, physical = CC._read_index(archive)
    base = CC._compact_index(index)
    paths = NUM._prefix_rows_to_paths(base["p"])

    numeric_rows, numeric_count = NUM._encode_numeric_paths(paths)
    numeric_candidate = {key: value for key, value in base.items() if key != "p"}
    numeric_candidate["pn"] = numeric_rows
    numeric_packed = msgpack.packb(numeric_candidate, use_bin_type=True)
    numeric_bytes, numeric_level = _compressed_size(numeric_packed)

    suffixes = _suffix_table(paths)
    hybrid_rows, hybrid_numeric_count, suffix_count = _encode_hybrid_paths(paths, suffixes)
    hybrid_candidate = {key: value for key, value in base.items() if key != "p"}
    hybrid_candidate["ph"] = hybrid_rows
    hybrid_candidate["sx"] = suffixes
    hybrid_packed = msgpack.packb(hybrid_candidate, use_bin_type=True)
    hybrid_bytes, hybrid_level = _compressed_size(hybrid_packed)

    decoded_paths = _decode_hybrid_paths(hybrid_candidate["ph"], hybrid_candidate["sx"])
    restored = dict(hybrid_candidate)
    restored.pop("ph")
    restored.pop("sx")
    restored["p"] = NUM._paths_to_prefix_rows(decoded_paths)
    expanded = CC._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("suffix-table compact control does not expand exactly to shipping r24 index")

    base_result = CC._compact_once(archive)
    base_bytes = int(base_result["compact_index_comp_bytes_per_copy"])
    selected_bytes = min(base_bytes, numeric_bytes, hybrid_bytes)
    selected_kind = min(
        ((base_bytes, 0, "base"), (numeric_bytes, 1, "numeric"), (hybrid_bytes, 2, "suffix_hybrid")),
        key=lambda item: (item[0], item[1]),
    )[2]
    projected = int(physical["archive_bytes"]) - 2 * int(physical["index_comp_bytes_per_copy"]) + 2 * selected_bytes
    numeric_best = min(base_bytes, numeric_bytes)
    return {
        **physical,
        "base_compact_bytes_per_copy": base_bytes,
        "numeric_compact_bytes_per_copy": numeric_bytes,
        "numeric_level": numeric_level,
        "hybrid_compact_bytes_per_copy": hybrid_bytes,
        "hybrid_level": hybrid_level,
        "suffix_table": suffixes,
        "suffix_table_entries": len(suffixes),
        "suffix_rows": suffix_count,
        "hybrid_numeric_rows": hybrid_numeric_count,
        "numeric_rows": numeric_count,
        "path_rows": len(paths),
        "selected_kind": selected_kind,
        "selected_compact_bytes_per_copy": selected_bytes,
        "projected_archive_bytes": projected,
        "saving_vs_shipping_bytes": int(physical["archive_bytes"]) - projected,
        "incremental_saving_vs_numeric_bytes": 2 * max(0, numeric_best - hybrid_bytes),
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
    if len(roots) != 15:
        raise RuntimeError(f"expected exact 15-workload corpus, got {len(roots)}")

    rows = []
    regressions = []
    incremental_rows = []
    aggregate_shipping = 0
    aggregate_projected = 0
    aggregate_incremental = 0

    for name in sorted(roots):
        archive = work_root / "archives" / f"{name}.cmpct"
        stats, verified = _shipping(roots[name], archive)
        result = _hybrid_compact_once(archive)
        row = {
            "workload": name,
            "shipping_bytes": int(result["archive_bytes"]),
            "projected_bytes": int(result["projected_archive_bytes"]),
            "saving_bytes": int(result["saving_vs_shipping_bytes"]),
            "incremental_saving_vs_numeric_bytes": int(result["incremental_saving_vs_numeric_bytes"]),
            "base_compact_bytes_per_copy": int(result["base_compact_bytes_per_copy"]),
            "numeric_compact_bytes_per_copy": int(result["numeric_compact_bytes_per_copy"]),
            "hybrid_compact_bytes_per_copy": int(result["hybrid_compact_bytes_per_copy"]),
            "selected_kind": result["selected_kind"],
            "suffix_table_entries": int(result["suffix_table_entries"]),
            "suffix_rows": int(result["suffix_rows"]),
            "path_rows": int(result["path_rows"]),
            "tree_sha256": verified.get("tree_sha256"),
            "dead_dictionary_elision": stats.get("r24_dead_dictionary_elision"),
            "semantic_index_roundtrip_exact": bool(result["semantic_index_roundtrip_exact"]),
            "two_control_copies": bool(result["two_authenticated_control_copies_retained"]),
            "payload_records_unchanged": bool(result["payload_records_unchanged"]),
        }
        aggregate_shipping += row["shipping_bytes"]
        aggregate_projected += row["projected_bytes"]
        aggregate_incremental += row["incremental_saving_vs_numeric_bytes"]
        if row["projected_bytes"] > row["shipping_bytes"]:
            regressions.append(name)
        if row["incremental_saving_vs_numeric_bytes"] > 0:
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
    promotion_signal = bool(experiment_valid and aggregate_incremental > 0)
    return {
        "schema": "cmpct-v030-r24-suffix-path-control-v1",
        "contract": {
            "workloads": 15,
            "policy_inputs": ["previous_canonical_path", "current_canonical_path", "canonical_path_suffix_frequency"],
            "forbidden_policy_inputs": ["benchmark_name", "workload_label", "filename_literal", "path_literal", "content_hash"],
            "suffix_rule": "intern repeated canonical PurePosixPath suffixes (4+ uses), then choose the smallest local literal/numeric/suffix token and the smallest complete compressed base/numeric/hybrid control plane",
            "max_suffixes": MAX_SUFFIXES,
            "two_authenticated_control_copies_retained": True,
            "physical_payload_records_unchanged": True,
            "release_credit": False,
        },
        "rows": rows,
        "summary": {
            "aggregate_shipping_bytes": aggregate_shipping,
            "aggregate_projected_bytes": aggregate_projected,
            "aggregate_saving_vs_shipping_bytes": aggregate_shipping - aggregate_projected,
            "aggregate_incremental_saving_vs_numeric_bytes": aggregate_incremental,
            "suffix_selected_workloads": incremental_rows,
            "regressions": regressions,
            "encrypted_like_incremental_saving_bytes": target["incremental_saving_vs_numeric_bytes"],
            "encrypted_like_projected_bytes": target["projected_bytes"],
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
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-suffix-path-control-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-suffix-path-control.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("suffix-table compact-control experiment invalid")


if __name__ == "__main__":
    main()
