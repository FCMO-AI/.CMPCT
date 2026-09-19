from __future__ import annotations

"""Research-only physical byte-floor oracle for locality-safe C25CC01.

The locality-pack search has already shown that deterministic bin ordering changes the encrypted-like candidate by
only tens of bytes while preserving the hard <=8x selected-member amplification law. This oracle asks the more useful
architectural question: with that locality-safe r24 physical data span held byte-for-byte fixed, can *any* control
encoding in the current C25CC01 envelope still beat solid Zstd-19?

The floor deliberately gives the current grammar an impossible advantage: both authenticated control copies are
priced at zero bytes. If even ``HDR + physical_data + FTR`` cannot beat Zstd-19, control-map work is mathematically
futile and the physical record grammar must change. If the floor does beat Zstd-19, the receipt reports the exact
combined control-byte budget available for a strict win and how much of the current duplicated compact control must
still be removed. No benchmark identity enters product code; this target-scoped research lane grants zero release or
selector credit.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"


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

    fixed_framing_bytes = int(R24.HDR.size + R24.FTR.size)
    physical_data_bytes = int(physical["data_bytes"])
    zero_control_floor_bytes = fixed_framing_bytes + physical_data_bytes
    reconstructed_current_bytes = zero_control_floor_bytes + 2 * len(compact_comp)
    if reconstructed_current_bytes != int(row["wrapped_bytes"]):
        raise RuntimeError(
            "C25 physical-floor accounting drift: "
            f"reconstructed={reconstructed_current_bytes} measured={row['wrapped_bytes']}"
        )

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])

    # Strictly smaller means equality is not enough: reserve one byte below the competitor before allocating any
    # control bytes. A negative budget proves the current physical span cannot possibly satisfy the size contract.
    strict_total_control_budget = zstd_bytes - 1 - zero_control_floor_bytes
    current_total_control_bytes = 2 * len(compact_comp)
    required_control_reduction = max(0, current_total_control_bytes - strict_total_control_budget)
    floor_margin = zstd_bytes - zero_control_floor_bytes

    return {
        "schema": "cmpct-v030-c25cc01-physical-floor-oracle-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "candidate": {
            "r24_bytes": int(row["r24_bytes"]),
            "wrapped_bytes": int(row["wrapped_bytes"]),
            "tree_sha256": row["tree_sha256"],
            "locality": row["locality"],
            "physical_data_bytes": physical_data_bytes,
            "fixed_header_footer_bytes": fixed_framing_bytes,
            "compact_control_raw_bytes": len(compact_raw),
            "compact_control_level": int(compact_level),
            "compact_control_bytes_per_copy": len(compact_comp),
            "current_total_control_bytes": current_total_control_bytes,
            "source_index_bytes_per_copy": int(physical["index_comp_bytes_per_copy"]),
        },
        "zstd19_bytes": zstd_bytes,
        "zero_control_physical_floor_bytes": zero_control_floor_bytes,
        "physical_floor_margin_below_zstd_bytes": floor_margin,
        "strict_total_control_budget_bytes": strict_total_control_budget,
        "required_control_reduction_bytes": required_control_reduction,
        "required_control_reduction_fraction": (
            required_control_reduction / current_total_control_bytes if current_total_control_bytes else 0.0
        ),
        "gate": {
            "exact_wrapped_accounting": reconstructed_current_bytes == int(row["wrapped_bytes"]),
            "locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "zero_control_physical_floor_beats_zstd19": zero_control_floor_bytes < zstd_bytes,
            "current_control_fits_strict_zstd_budget": current_total_control_bytes <= strict_total_control_budget,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Target-scoped research lower bound only. Zero-byte control is intentionally impossible and is used to "
            "decide whether the unchanged locality-safe physical span leaves any theoretical room below Zstd-19. "
            "No product selector, archive grammar, locality threshold, benchmark threshold or release authority changes."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-physical-floor-work"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-physical-floor.json"),
    )
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("C25CC01 physical-floor oracle invalid")


if __name__ == "__main__":
    main()
