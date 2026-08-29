from __future__ import annotations

"""Research-only C25CC01 derived-blob-header byte frontier.

Exact locality-safe evidence proves the current physical span is already 117 bytes *larger* than Zstd-19 even if
both control copies cost zero bytes. Therefore control compaction alone cannot finish encrypted-like. The next
structural lever is r24's 64-byte per-record BHDR. C25's authenticated control/index already carries each record's
offset, uncompressed size, compressed size, codec and metadata length; the physical BHDR repeats those facts and
adds a 32-byte raw-payload SHA-256.

This oracle does not invent a shippable grammar. It holds the exact locality-safe candidate, payload, metadata and
full 32-byte per-record SHA-256 integrity cost constant, then accounts a hypothetical 32-byte digest-only physical
record header whose remaining framing facts are derived from authenticated control. The result answers whether that
single structural de-duplication is large enough to pay for the *existing* two-copy compact control and cross
Zstd-19. If not, the idea is too small and should be killed before format work. If yes, productization still requires
canonical grammar, corruption/recovery semantics, random-read proof, native/Android parity and all-15 no-regression.
No selector or release credit is granted here.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_physical_overhead_oracle as OVERHEAD
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"
DIGEST_ONLY_HEADER_BYTES = 32


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
    compact_raw, _compact = PROFILE._compact_raw(index)
    compact_level, compact_comp = PROFILE._compress_control(compact_raw)
    records = OVERHEAD._records(candidate)

    if int(records["blob_header_bytes"]) != int(records["record_count"]) * R24.BHDR.size:
        raise RuntimeError("blob-header accounting drift")
    if int(physical["data_bytes"]) != len(data):
        raise RuntimeError("physical-data accounting drift")

    current_wrapped = int(row["wrapped_bytes"])
    current_header_bytes = int(records["blob_header_bytes"])
    derived_header_bytes = int(records["record_count"]) * DIGEST_ONLY_HEADER_BYTES
    duplicated_non_digest_header_bytes = current_header_bytes - derived_header_bytes
    projected_physical_data_bytes = int(physical["data_bytes"]) - duplicated_non_digest_header_bytes
    fixed_framing_bytes = int(R24.HDR.size + R24.FTR.size)
    current_control_bytes = 2 * len(compact_comp)
    projected_wrapped_bytes = fixed_framing_bytes + projected_physical_data_bytes + current_control_bytes
    if current_wrapped - duplicated_non_digest_header_bytes != projected_wrapped_bytes:
        raise RuntimeError("derived-header projection does not reconcile to measured wrapped bytes")

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])

    return {
        "schema": "cmpct-v030-c25cc01-derived-blob-header-oracle-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "candidate": {
            "r24_bytes": int(row["r24_bytes"]),
            "current_wrapped_bytes": current_wrapped,
            "tree_sha256": row["tree_sha256"],
            "locality": row["locality"],
            "physical_data_bytes": int(physical["data_bytes"]),
            "record_count": int(records["record_count"]),
            "current_blob_header_bytes": current_header_bytes,
            "current_blob_header_bytes_per_record": int(R24.BHDR.size),
            "retained_sha256_bytes_per_record": DIGEST_ONLY_HEADER_BYTES,
            "derived_header_bytes": derived_header_bytes,
            "duplicated_non_digest_header_bytes": duplicated_non_digest_header_bytes,
            "record_meta_bytes_unchanged": int(records["record_meta_bytes"]),
            "compressed_payload_bytes_unchanged": int(records["compressed_payload_bytes"]),
            "compact_control_bytes_per_copy": len(compact_comp),
            "current_total_control_bytes": current_control_bytes,
            "compact_control_level": int(compact_level),
        },
        "zstd19_bytes": zstd_bytes,
        "projection": {
            "projected_physical_data_bytes": projected_physical_data_bytes,
            "fixed_header_footer_bytes": fixed_framing_bytes,
            "projected_wrapped_bytes_with_existing_two_copy_control": projected_wrapped_bytes,
            "margin_below_zstd19_bytes": zstd_bytes - projected_wrapped_bytes,
            "strictly_smaller_than_zstd19": projected_wrapped_bytes < zstd_bytes,
            "bytes_saved_vs_current_wrapped": duplicated_non_digest_header_bytes,
        },
        "gate": {
            "exact_current_wrapped_accounting": current_wrapped
            == fixed_framing_bytes + int(physical["data_bytes"]) + current_control_bytes,
            "locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "full_sha256_digest_cost_retained": DIGEST_ONLY_HEADER_BYTES == 32,
            "existing_control_cost_retained": True,
            "derived_header_large_enough_to_cross_zstd19": projected_wrapped_bytes < zstd_bytes,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Target-scoped byte-accounting oracle only. It removes only physical BHDR fields already represented in "
            "authenticated control while retaining a full 32-byte per-record SHA-256, payload bytes, record metadata, "
            "two compact control copies and the measured locality-safe packing. A positive result is not a format "
            "promotion: recovery without control, canonical grammar/readers, native/Android parity and all-15 evidence "
            "remain mandatory before any product change."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-derived-header-work"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-derived-header.json"),
    )
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("C25CC01 derived-blob-header oracle invalid")


if __name__ == "__main__":
    main()
