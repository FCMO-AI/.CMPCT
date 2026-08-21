from __future__ import annotations

"""Exact r24 A/B oracle for locality-bounded medium binary micro-packs.

The shipping r24 grammar already supports S_PACK slices, but the encoder currently limits micro-packing to
<=32 KiB text-like blobs. The locality-bounded solid research lane found strict size+creation wins on hostile
families made of ~64-130 KiB .bin members. This oracle asks the narrowest useful question: can the *existing r24
grammar* recover that cross-file redundancy by admitting medium .bin blobs to the same bounded pack mechanism?

This is research evidence only. It cannot authorize a release or widen shipping admission by itself. Promotion
requires exact byte/tree verification, no regression on the negative control, and complete-boundary wins against
ZIP/Deflate-9 and solid tar+Zstd-19 on the positive rows.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_release_product as P

MEDIUM_MAX = 256 * 1024
TARGETS = (
    ("resemblance_hostile_v1/02_false_neighbors", "hostile", "02_false_neighbors", True),
    ("resemblance_hostile_v1/05_incompressible", "hostile", "05_incompressible", True),
    # Negative control: another high-entropy family where current r24 loses size to Zstd. A generic binary-pack
    # policy must not make this row larger than today's r24 even if it cannot close the Zstd frontier yet.
    ("neutral_hostile_v1/07_incompressible_and_encrypted_like", "neutral", "07_incompressible_and_encrypted_like", False),
)


def _verified_r24(root: Path, out: Path, *, binary_pack: bool) -> dict:
    old_max = P.R24_RELEASE_MICRO_MAX_FILE_BYTES
    old_text = P.R24_BUILDER_MODULE.TEXT_EXT
    try:
        P.R24_RELEASE_MICRO_MAX_FILE_BYTES = MEDIUM_MAX if binary_pack else old_max
        if binary_pack:
            P.R24_BUILDER_MODULE.TEXT_EXT = set(old_text) | {".bin"}
        started = time.perf_counter()
        stats = P._locality_bounded_r24_build(root, out)
        build_s = time.perf_counter() - started
        started = time.perf_counter()
        verified = P.strong_verify(out)
        verify_s = time.perf_counter() - started
    finally:
        P.R24_RELEASE_MICRO_MAX_FILE_BYTES = old_max
        P.R24_BUILDER_MODULE.TEXT_EXT = old_text
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"r24 strong verification failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "build_s": build_s,
        "verify_s": verify_s,
        "complete_create_s": build_s + verify_s,
        "tree_sha256": verified.get("tree_sha256"),
        "micro_pack_max_file_bytes": int(stats["micro_pack_max_file_release_bytes"]),
        "micro_pack_target_bytes": int(stats["micro_pack_target_release_bytes"]),
        "release_byte_knobs": stats.get("release_byte_knobs"),
    }


def _comparators(root: Path, work: Path) -> dict:
    zip_path = work / "cmp.zip"
    zstd_path = work / "cmp.tar.zst"
    zip_out = work / "zip-out"
    zstd_out = work / "zstd-out"
    z = EXT._zip(root, zip_path, zip_out)
    s = EXT._tar_zstd(root, zstd_path, zstd_out, work)
    return {"zip_deflate9": z, "tar_zstd19_solid": s}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral_root = work_root / "neutral"
    hostile_root = work_root / "hostile"
    # The neutral corpus must be generated through the accepted repair-v6 hooks before any row is measured.
    # Installing the hooks after generation would silently benchmark an obsolete tree identity.
    REPAIR.install_generation_hooks(NEUTRAL)
    NEUTRAL.build(neutral_root)
    REPAIR.normalize_root(neutral_root)
    HOSTILE.build(hostile_root)

    rows = []
    for label, suite, name, positive in TARGETS:
        source = (neutral_root if suite == "neutral" else hostile_root) / name
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-r24-medium-pack-", dir=work_root) as td:
            w = Path(td)
            baseline = _verified_r24(source, w / "baseline.cmpct", binary_pack=False)
            candidate = _verified_r24(source, w / "candidate.cmpct", binary_pack=True)
            comps = _comparators(source, w)
        same_tree = baseline["tree_sha256"] == candidate["tree_sha256"]
        no_r24_byte_regression = candidate["archive_bytes"] <= baseline["archive_bytes"]
        beats_zip_size = candidate["archive_bytes"] < comps["zip_deflate9"]["archive_bytes"]
        beats_zstd_size = candidate["archive_bytes"] < comps["tar_zstd19_solid"]["archive_bytes"]
        beats_zip_create = candidate["complete_create_s"] < comps["zip_deflate9"]["create_s"]
        beats_zstd_create = candidate["complete_create_s"] < comps["tar_zstd19_solid"]["create_s"]
        strict_four_way = beats_zip_size and beats_zstd_size and beats_zip_create and beats_zstd_create
        row = {
            "label": label,
            "positive_target": positive,
            "baseline_r24": baseline,
            "medium_binary_pack_r24": candidate,
            "comparators": comps,
            "same_verified_tree": same_tree,
            "saving_vs_baseline_r24_bytes": baseline["archive_bytes"] - candidate["archive_bytes"],
            "no_r24_byte_regression": no_r24_byte_regression,
            "beats_zip_size": beats_zip_size,
            "beats_zstd19_size": beats_zstd_size,
            "beats_zip_create": beats_zip_create,
            "beats_zstd19_create": beats_zstd_create,
            "strict_four_way_win": strict_four_way,
        }
        rows.append(row)
        print(json.dumps({"label": label, "saving": row["saving_vs_baseline_r24_bytes"], "four_way": strict_four_way}, separators=(",", ":")), flush=True)

    positives = [r for r in rows if r["positive_target"]]
    controls = [r for r in rows if not r["positive_target"]]
    gate = {
        "all_verified_tree_equal": all(r["same_verified_tree"] for r in rows),
        "all_rows_no_r24_byte_regression": all(r["no_r24_byte_regression"] for r in rows),
        "positive_rows_strict_four_way": all(r["strict_four_way_win"] for r in positives),
        "negative_controls_no_r24_byte_regression": all(r["no_r24_byte_regression"] for r in controls),
    }
    gate["promotion_recommended"] = all(gate.values())
    return {
        "schema": "cmpct-v030-r24-medium-binary-pack-oracle-v1",
        "contract": {
            "grammar": "existing canonical r24 S_PACK only",
            "candidate_micro_pack_max_file_bytes": MEDIUM_MAX,
            "candidate_extra_pack_hints": [".bin"],
            "locality_policy": "shipping r24 micro_pack_target remains min(2 MiB, 8x largest regular member)",
            "promotion_rule": "both positive rows strict size+complete-create wins vs ZIP and Zstd-19; no tested r24 byte regression",
        },
        "rows": rows,
        "gate": gate,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-medium-pack-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-medium-pack.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate"], indent=2), flush=True)
    if not result["gate"]["promotion_recommended"]:
        raise SystemExit("medium binary r24 pack did not earn promotion")


if __name__ == "__main__":
    main()
