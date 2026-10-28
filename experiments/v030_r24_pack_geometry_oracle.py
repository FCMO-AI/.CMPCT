from __future__ import annotations

"""Diagnostic oracle for canonical-r24 packing geometry.

This experiment exists to answer one narrow causal question raised by the canonical v0.30
15-workload failure: how much of the shipping r24 fallback byte debt is caused by each of the
three encoder-policy changes that are deliberately *not* part of frozen v0.29 evidence?

The oracle prices complete revision-24 artifacts on the exact repaired 15-workload corpus and
measures the public selected-member locality operation.  It changes no grammar, baseline,
release threshold or product selector and receives zero release credit.

Variants are ablations of the shipping r24-v4 encoder policy:

* shipping: current canonical fallback policy.
* default-pack-target: keep shipping max-file / medium-bin / Deflate / large-file policies but
  restore Builder's mature 256 KiB micro-pack target.
* default-pack-max-file: keep shipping target / medium-bin / Deflate / large-file policies but
  restore Builder's mature 32 KiB maximum file admitted to micro-packs.
* no-medium-bin-pack: keep shipping target / max-file / Deflate / large-file policies but stop
  treating .bin as text-like solely for S_PACK admission.

A useful result must point to a measured owner.  If no single ablation recovers material bytes,
the pack-geometry hypothesis is narrowed and work should move to a different representation or
fallback owner rather than threshold-gardening these knobs.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_release_generalization as GATE
from benchmarks.v030_release_generalization_canonical import _r24_selected_member_amplification
from experiments import entropygraph_v030_release_product_base as BASE

ENGINE = "v030-r24-pack-geometry-oracle-v1"
MAX_MEMBER_READ_AMP = 8.0


def _build_variant(root: Path, out: Path, variant: str) -> dict:
    root = Path(root)
    out = Path(out)
    started = time.perf_counter()
    builder = BASE.C.Builder(root, deflate_reuse_min=BASE.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    mature_target = int(builder.micro_pack_target)
    mature_max_file = int(builder.micro_pack_max_file)
    regular_files, largest_member = BASE._regular_user_shape(root)
    shipping_target = mature_target
    if largest_member > 0:
        shipping_target = min(BASE.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member)

    builder.micro_pack_target = shipping_target
    builder.micro_pack_max_file = BASE.R24_RELEASE_MICRO_MAX_FILE_BYTES
    medium_binary = True

    if variant == "default-pack-target":
        builder.micro_pack_target = mature_target
    elif variant == "default-pack-max-file":
        builder.micro_pack_max_file = mature_max_file
    elif variant == "no-medium-bin-pack":
        medium_binary = False
    elif variant != "shipping":
        raise ValueError(f"unknown variant {variant!r}")

    wide_single_file = regular_files == 1 and largest_member >= BASE.R24_RELEASE_WIDE_CHUNK_BYTES
    previous_wide = getattr(BASE._R24_CDC_POLICY, "wide_single_file", False)
    previous_medium = getattr(BASE._R24_CDC_POLICY, "medium_binary_pack", False)
    BASE._R24_CDC_POLICY.wide_single_file = wide_single_file
    BASE._R24_CDC_POLICY.medium_binary_pack = medium_binary
    try:
        stats = dict(builder.build(out))
    finally:
        BASE._R24_CDC_POLICY.wide_single_file = previous_wide
        BASE._R24_CDC_POLICY.medium_binary_pack = previous_medium

    verified = BASE.strong_verify(out)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"r24 oracle strong verification failed: {verified!r}")
    amp = float(_r24_selected_member_amplification(out))
    return {
        "archive_bytes": out.stat().st_size,
        "create_s": time.perf_counter() - started,
        "selected_member_amplification": amp,
        "locality_pass": amp <= MAX_MEMBER_READ_AMP,
        "micro_pack_target_bytes": int(builder.micro_pack_target),
        "micro_pack_max_file_bytes": int(builder.micro_pack_max_file),
        "medium_binary_pack": medium_binary,
        "deflate_reuse_min_bytes": BASE.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
        "wide_single_file": wide_single_file,
        "regular_files": regular_files,
        "largest_regular_member_bytes": largest_member,
        "strong_verify": verified,
        "builder_stats": stats,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GATE._accepted_v029_rows()

    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_pack_geometry_neutral")
    hostile = V029._load(V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_pack_geometry_hostile")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_v030_pack_geometry_repair_v6")
    repair.install_generation_hooks(neutral)

    variants = ("shipping", "default-pack-target", "default-pack-max-file", "no-medium-bin-pack")
    rows: list[dict] = []
    for suite, corpus, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        corpus.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            expected = accepted[(suite, workload.name)]
            historical_tree = GATE._historical_treehash(workload)
            if historical_tree != expected["tree_sha256"]:
                raise RuntimeError(
                    f"historical source drift for {suite}/{workload.name}: "
                    f"{historical_tree} != {expected['tree_sha256']}"
                )
            row = {
                "suite": suite,
                "name": workload.name,
                "historical_tree_sha256": historical_tree,
                "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
                "variants": {},
            }
            with tempfile.TemporaryDirectory(prefix="cmpct-r24-pack-oracle-", dir=work_root) as td:
                td = Path(td)
                for variant in variants:
                    row["variants"][variant] = _build_variant(workload, td / f"{variant}.cmpct", variant)
            shipping = int(row["variants"]["shipping"]["archive_bytes"])
            row["shipping_regression_vs_v029_bytes"] = shipping - row["accepted_v029_bytes"]
            for variant in variants[1:]:
                measured = row["variants"][variant]
                measured["recovery_vs_shipping_bytes"] = shipping - int(measured["archive_bytes"])
            rows.append(row)
            print(json.dumps({
                "suite": suite,
                "name": workload.name,
                "accepted_v029": row["accepted_v029_bytes"],
                "shipping": shipping,
                "shipping_regression": row["shipping_regression_vs_v029_bytes"],
                "ablations": {
                    v: {
                        "bytes": row["variants"][v]["archive_bytes"],
                        "recovery": row["variants"][v].get("recovery_vs_shipping_bytes", 0),
                        "amp": row["variants"][v]["selected_member_amplification"],
                    }
                    for v in variants
                },
            }), flush=True)

    if len(rows) != 15:
        raise RuntimeError(f"expected 15 workloads, got {len(rows)}")

    totals = {}
    accepted_total = sum(int(row["accepted_v029_bytes"]) for row in rows)
    for variant in variants:
        archive_total = sum(int(row["variants"][variant]["archive_bytes"]) for row in rows)
        totals[variant] = {
            "archive_bytes": archive_total,
            "delta_vs_accepted_v029_bytes": archive_total - accepted_total,
            "recovery_vs_shipping_bytes": 0,
            "workloads_smaller_than_shipping": 0,
            "workloads_larger_than_shipping": 0,
            "locality_failures": sum(not row["variants"][variant]["locality_pass"] for row in rows),
            "max_selected_member_amplification": max(
                float(row["variants"][variant]["selected_member_amplification"]) for row in rows
            ),
        }
    shipping_total = totals["shipping"]["archive_bytes"]
    for variant in variants[1:]:
        totals[variant]["recovery_vs_shipping_bytes"] = shipping_total - totals[variant]["archive_bytes"]
        totals[variant]["workloads_smaller_than_shipping"] = sum(
            row["variants"][variant]["archive_bytes"] < row["variants"]["shipping"]["archive_bytes"] for row in rows
        )
        totals[variant]["workloads_larger_than_shipping"] = sum(
            row["variants"][variant]["archive_bytes"] > row["variants"]["shipping"]["archive_bytes"] for row in rows
        )

    return {
        "engine": ENGINE,
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "complete-r24-artifact byte/locality attribution for pack-geometry policy only",
        "contract": {
            "workloads": 15,
            "accepted_v029_aggregate_bytes": GATE.EXPECTED_V029_TOTAL,
            "maximum_selected_member_read_amplification": MAX_MEMBER_READ_AMP,
            "baseline_and_release_thresholds_unchanged": True,
            "no_product_policy_changes": True,
        },
        "totals": totals,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/r24-pack-geometry-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/r24-pack-geometry.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2), flush=True)


if __name__ == "__main__":
    main()
