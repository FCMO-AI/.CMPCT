from __future__ import annotations

"""Research-only distributed blob-table feasibility oracle for encrypted-like.

Exact-head physical-floor evidence proves that the current locality-safe r24 physical span cannot beat solid
Zstd-19 even if both central control copies cost zero. Separately, the salvage-preserving varint-header oracle shows
that shortening the 64-byte BHDR alone is still nowhere near enough while the full compact blob table remains in both
control copies.

This experiment attacks the duplicated information rather than either surface independently. In canonical r24 every
``index['blobs']`` row is ``[offset, usize, csize, codec, meta_len]``. Those five values are already derivable from a
sequential walk of the self-describing physical records: offset is cumulative, and the other four fields are present
in each BHDR. A future grammar can therefore reconstruct the blob table from the physical stream and omit it from
both authenticated semantic-root copies.

The projection combines two independently fail-closed ideas:
- retain a salvage-preserving per-record header (magic, codec, flags, usize/csize/meta_len, CRC32, SHA-256), using the
  exact varint accounting already audited by the derived-header oracle;
- omit only the duplicated central ``b`` table, reconstruct it from physical records, then prove the ordinary compact
  control expands exactly to the original r24 semantic index.

No archive bytes are emitted and no selector/release credit is granted. A positive size result is only a signal to
implement a hostile-input-safe physical grammar and reader; a negative result kills this combined family too.
"""

import argparse
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_derived_blob_header_oracle as HEADER
from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from benchmarks import v030_r24_physical_overhead_oracle as OVERHEAD
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"


def _derived_blob_table(data: bytes) -> list[list[int]]:
    """Reconstruct the exact r24 blob table from contiguous self-describing records."""
    rows: list[list[int]] = []
    off = 0
    while off < len(data):
        if off + R24.BHDR.size > len(data):
            raise RuntimeError("truncated physical record while deriving blob table")
        magic, codec, _flags, _reserved, usize, csize, meta_len, _crc32, _sha256 = R24.BHDR.unpack_from(data, off)
        if magic != R24.BMAGIC:
            raise RuntimeError(f"physical record lost resynchronization magic at offset {off}")
        usize = int(usize)
        csize = int(csize)
        codec = int(codec)
        meta_len = int(meta_len)
        if min(usize, csize, codec, meta_len) < 0:
            raise RuntimeError("negative physical record field")
        rows.append([off, usize, csize, codec, meta_len])
        next_off = off + R24.BHDR.size + meta_len + csize
        if next_off <= off or next_off > len(data):
            raise RuntimeError("physical record length escapes data span")
        off = next_off
    if off != len(data):
        raise RuntimeError("physical record derivation did not consume exact data span")
    return rows


def _compress_root_without_blobs(index: dict, derived_blobs: list[list[int]]) -> dict:
    compact = CONTROL._compact_index(index)
    if compact.get("b") != derived_blobs:
        raise RuntimeError("compact blob table differs from physical-derived table")
    root = dict(compact)
    root.pop("b")
    envelope = {"x": list(index["features"]), "c": root}
    raw = msgpack.packb(envelope, use_bin_type=True)
    level, comp = PROFILE._compress_control(raw)

    # Reader-side reconstruction proof: restore only the physically-derived table, then use the existing exact
    # compact-control expander. This must reproduce the source semantic index byte-semantically.
    reconstructed_compact = dict(root)
    reconstructed_compact["b"] = derived_blobs
    expanded = CONTROL._expand_index(
        reconstructed_compact,
        version=int(index["v"]),
        features=list(index["features"]),
    )
    if expanded != index:
        raise RuntimeError("distributed blob-table root does not reconstruct exact semantic index")
    return {
        "raw_bytes": len(raw),
        "compressed_bytes": len(comp),
        "level": int(level),
        "exact_semantic_index_reconstruction": True,
    }


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
    derived_blobs = _derived_blob_table(data)
    if derived_blobs != index.get("blobs"):
        raise RuntimeError("physical stream cannot exactly derive source r24 blob table")

    root = _compress_root_without_blobs(index, derived_blobs)
    salvage = HEADER._salvage_header_accounting(index, data)
    records = OVERHEAD._records(candidate)
    if int(records["record_count"]) != len(derived_blobs) or int(salvage["record_count"]) != len(derived_blobs):
        raise RuntimeError("distributed-control record count disagreement")

    current_header_bytes = int(records["blob_header_bytes"])
    projected_physical_data_bytes = int(physical["data_bytes"]) - current_header_bytes + int(salvage["header_bytes"])
    fixed_framing_bytes = int(R24.HDR.size + R24.FTR.size)
    projected_total_control_bytes = 2 * int(root["compressed_bytes"])
    projected_archive_bytes = fixed_framing_bytes + projected_physical_data_bytes + projected_total_control_bytes

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])

    # Also expose the exact budget remaining for *both* authenticated semantic-root copies after the salvage-safe
    # physical framing is priced. This makes a negative result useful rather than merely red.
    strict_total_control_budget = zstd_bytes - 1 - fixed_framing_bytes - projected_physical_data_bytes

    return {
        "schema": "cmpct-v030-c25cc01-distributed-blob-control-oracle-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "candidate": {
            "r24_bytes": int(row["r24_bytes"]),
            "current_wrapped_bytes": int(row["wrapped_bytes"]),
            "tree_sha256": row["tree_sha256"],
            "locality": row["locality"],
            "record_count": len(derived_blobs),
            "current_physical_data_bytes": int(physical["data_bytes"]),
            "current_blob_header_bytes": current_header_bytes,
            "compressed_payload_plus_meta_bytes": int(physical["data_bytes"]) - current_header_bytes,
        },
        "distributed_root": root,
        "salvage_header_accounting": salvage,
        "projection": {
            "fixed_header_footer_bytes": fixed_framing_bytes,
            "projected_physical_data_bytes": projected_physical_data_bytes,
            "two_authenticated_blobless_root_bytes": projected_total_control_bytes,
            "strict_total_control_budget_bytes": strict_total_control_budget,
            "projected_archive_bytes": projected_archive_bytes,
        },
        "zstd19_bytes": zstd_bytes,
        "margin_below_zstd19_bytes": zstd_bytes - projected_archive_bytes,
        "gate": {
            "physical_blob_table_exactly_derivable": derived_blobs == index.get("blobs"),
            "semantic_index_roundtrip_exact": bool(root["exact_semantic_index_reconstruction"]),
            "locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "salvage_self_description_retained": all(
                salvage[k] is True for k in (
                    "retains_magic", "retains_codec", "retains_flags", "retains_usize", "retains_csize",
                    "retains_meta_len", "retains_crc32", "retains_sha256",
                )
            ),
            "two_authenticated_semantic_roots_priced": True,
            "strictly_smaller_than_zstd19": projected_archive_bytes < zstd_bytes,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Target-scoped research projection only. It proves whether a distributed blob-table grammar has enough "
            "byte budget to justify implementation. It does not emit a new archive or prove hostile resynchronization, "
            "recovery after arbitrary record damage, creation speed, native/Android parity, all-15 no-regression, or "
            "release readiness. No selector or benchmark threshold changes."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-distributed-control-work"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-distributed-control.json"),
    )
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("distributed blob-table control oracle invalid")


if __name__ == "__main__":
    main()
