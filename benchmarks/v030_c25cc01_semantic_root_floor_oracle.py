from __future__ import annotations

"""Research-only semantic-root floor for the encrypted-like C25 frontier.

Exact-head evidence proves the current locality-safe physical span cannot beat Zstd-19 even with zero control, while
a salvage-preserving varint record header can recover only a few KiB. The remaining question is whether a *new*
self-describing physical grammar could move storage coordinates into each recoverable physical record and leave a
small enough duplicated logical/recovery root to fit below Zstd-19.

This oracle does not claim such a grammar exists. It measures the irreducible logical facts that cannot be derived
from self-describing payload records: canonical paths, file kinds, mode/mtime overrides, hardlink ownership,
filesystem metadata and feature identity. It also decomposes the current compact-control object field-by-field and
prices two authenticated copies of that semantic root against the salvage-header physical projection. Storage
coordinates, logical sizes and payload digests are intentionally excluded from the semantic root only under the
explicit hypothetical assumption that a future physical record grammar carries/reconstructs them itself.

A negative result kills that architecture family. A positive result only establishes byte headroom; exact recovery,
hostile resynchronization, locality, canonical semantics, native/Android parity, timing and all-15 authority remain
mandatory before any product change.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_derived_blob_header_oracle as DERIVED
from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_physical_overhead_oracle as OVERHEAD
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"
LEVELS = PROFILE.LEVELS


def _best_compressed(obj) -> dict:
    raw = msgpack.packb(obj, use_bin_type=True)
    rows = []
    for level in LEVELS:
        comp = R24.zc(raw, level)
        rows.append((len(comp), int(level)))
    size, level = min(rows)
    return {"raw_bytes": len(raw), "compressed_bytes": int(size), "level": int(level)}


def _semantic_root(index: dict, compact: dict) -> dict:
    rows = []
    kind_counts: Counter[int] = Counter()
    for encoded in compact["f"]:
        kind = int(encoded[0])
        kind_counts[kind] += 1
        # Preserve only logical metadata that cannot be inferred from a self-describing physical payload. Hardlink
        # owner identity is logical metadata; ordinary storage coordinates/sizes/digests are deliberately omitted.
        if kind == R24.K_HARDLINK:
            rows.append([kind, encoded[1], encoded[2], int(encoded[3])])
        else:
            rows.append([kind, encoded[1], encoded[2]])
    root = {
        "x": list(index["features"]),
        "p": compact["p"],
        "d": compact["d"],
        "q": rows,
        "m": compact["m"],
    }
    return root, {str(k): int(v) for k, v in sorted(kind_counts.items())}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)

    candidate = work_root / "cmpct" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, candidate, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError(f"{STRATEGY_NAME} locality-safe candidate unexpectedly ineligible: {row!r}")

    index, data, physical = PROFILE._source_r24_parts(candidate)
    compact_raw, compact = PROFILE._compact_raw(index)
    compact_level, compact_comp = PROFILE._compress_control(compact_raw)
    records = OVERHEAD._records(candidate)
    salvage = DERIVED._salvage_header_accounting(index, data)

    root, kind_counts = _semantic_root(index, compact)
    root_size = _best_compressed(root)
    field_sizes = {key: _best_compressed({key: compact[key]}) for key in ("p", "d", "f", "b", "r", "z", "m")}
    drop_field_sizes = {}
    for key in ("p", "d", "f", "b", "r", "z", "m"):
        remainder = {k: v for k, v in compact.items() if k != key}
        drop_field_sizes[key] = _best_compressed(remainder)

    current_header_bytes = int(records["blob_header_bytes"])
    salvage_physical_data = int(physical["data_bytes"]) - current_header_bytes + int(salvage["header_bytes"])
    fixed_framing = int(R24.HDR.size + R24.FTR.size)

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])

    strict_two_copy_root_budget = zstd_bytes - 1 - fixed_framing - salvage_physical_data
    semantic_root_two_copy_bytes = 2 * int(root_size["compressed_bytes"])
    projected_semantic_floor = fixed_framing + salvage_physical_data + semantic_root_two_copy_bytes

    return {
        "schema": "cmpct-v030-c25cc01-semantic-root-floor-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "candidate": {
            "r24_bytes": int(row["r24_bytes"]),
            "current_wrapped_bytes": int(row["wrapped_bytes"]),
            "tree_sha256": row["tree_sha256"],
            "locality": row["locality"],
            "physical_data_bytes": int(physical["data_bytes"]),
            "record_count": int(records["record_count"]),
            "current_blob_header_bytes": current_header_bytes,
            "salvage_header_bytes": int(salvage["header_bytes"]),
            "salvage_projected_physical_data_bytes": salvage_physical_data,
            "current_control_raw_bytes": len(compact_raw),
            "current_control_bytes_per_copy": len(compact_comp),
            "current_control_level": int(compact_level),
            "kind_counts": kind_counts,
        },
        "zstd19_bytes": zstd_bytes,
        "semantic_root": {
            **root_size,
            "two_copy_bytes": semantic_root_two_copy_bytes,
            "strict_two_copy_budget_bytes": strict_two_copy_root_budget,
            "projected_floor_bytes": projected_semantic_floor,
            "margin_below_zstd19_bytes": zstd_bytes - projected_semantic_floor,
            "fits_strict_budget": semantic_root_two_copy_bytes <= strict_two_copy_root_budget,
            "assumption": (
                "future self-describing physical records reconstruct all storage coordinates, logical sizes and payload "
                "digests; duplicated root retains paths/kinds/mode/mtime/hardlinks/fsmeta/features only"
            ),
        },
        "current_compact_field_independent_sizes": field_sizes,
        "current_compact_drop_one_field_sizes": drop_field_sizes,
        "gate": {
            "exact_current_control_accounting": int(row["wrapped_bytes"])
            == fixed_framing + int(physical["data_bytes"]) + 2 * len(compact_comp),
            "locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "salvage_record_self_description_retained": all(
                salvage[k] is True for k in (
                    "retains_magic", "retains_codec", "retains_flags", "retains_usize", "retains_csize",
                    "retains_meta_len", "retains_crc32", "retains_sha256"
                )
            ),
            "semantic_root_family_has_byte_headroom": semantic_root_two_copy_bytes <= strict_two_copy_root_budget,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Target-scoped architecture floor only. The semantic-root projection deliberately assumes a future physical "
            "grammar can reconstruct storage mapping/size/digest facts from salvageable records; it does not prove that "
            "grammar or grant selector/product/release credit. A negative result rules out this family under the measured "
            "salvage-header floor; a positive result only authorizes implementation research."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-semantic-root-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-semantic-root.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("C25CC01 semantic-root floor invalid")


if __name__ == "__main__":
    main()
