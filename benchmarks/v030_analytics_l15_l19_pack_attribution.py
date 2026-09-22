from __future__ import annotations

"""Attribute the exhausted Analytics level-15 -> level-19 density gap by physical pack.

The accepted effort-frontier receipt showed level 15 is the strongest measured v0.25/CMPNX5
point inside ZIP's creation-time budget, while level 19 nearly reproduces the accepted v0.29
byte floor but is far too slow. Importantly, raising the cap from 15 to 19 does *not* alter
v0.25's Zstd-3 family probes, cold stream slabs, or Zstd-12 metadata. Therefore the physical
raw pack partition should remain byte-identical and only ordinary pack payload coding changes.

This referee builds both fixed caps once on the same normalized Analytics tree, proves their
raw physical pack identities are identical, and attributes every compressed-byte delta by the
logical roles that reference each pack. It is diagnostic only: no new representation, selector,
threshold, release, or format claim is made.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25

TARGET = "04_analytics_and_database"
LEVELS = (15, 19)


def _ref_pack_indices(refs) -> set[int]:
    out: set[int] = set()
    for ref in refs:
        if ref and ref[0] in ("slice", "whole"):
            out.add(int(ref[1]))
    return out


def _pack_labels(meta: dict, pack_count: int) -> dict[int, list[str]]:
    labels: dict[int, set[str]] = {i: set() for i in range(pack_count)}

    for stream_offset, pi, stream_len in meta.get("stream_packs", []):
        labels[int(pi)].add("stream_pool")

    for pi, entries in meta.get("micro", []):
        exts = sorted({Path(path).suffix.lower() or "<none>" for path, _n in entries})
        for ext in exts:
            labels[int(pi)].add(f"micro:{ext}")

    for path, desc in meta.get("files", []):
        typ = desc[0]
        refs = None
        if typ == "plain":
            refs = desc[1]
        elif typ == "zipstreams":
            refs = desc[1]  # skeleton only; member streams are separately labelled above
        elif typ == "splice":
            refs = desc[1]  # residual literal object
        if refs is not None:
            ext = Path(path).suffix.lower() or "<none>"
            for pi in _ref_pack_indices(refs):
                labels[pi].add(f"{typ}:{ext}")

    return {pi: sorted(vals) if vals else ["unreferenced_or_internal"] for pi, vals in labels.items()}


def _build(stage: Path, root: Path, level: int) -> dict:
    old_cap = CANON.LEVEL_CAP
    CANON.LEVEL_CAP = level
    try:
        result = CANON._canonical_v25(stage, root)
    finally:
        CANON.LEVEL_CAP = old_cap

    archive = root / "candidate.cmpnx5"
    V25.OUT = archive
    f, meta, po = V25.open_ar()
    try:
        labels = _pack_labels(meta, len(po))
        packs = []
        for pi, (_off, codec, usize, csize, crc, hh) in enumerate(po):
            packs.append({
                "pi": pi,
                "codec": int(codec),
                "usize": int(usize),
                "csize": int(csize),
                "crc32": int(crc),
                "sha256": bytes(hh).hex(),
                "labels": labels[pi],
            })
    finally:
        f.close()

    return {
        "archive_bytes": int(result["archive_bytes"]),
        "complete_verified_create_s": float(result["complete_verified_create_s"]),
        "build_stats": result["build_stats"],
        "meta_version": int(meta["v"]),
        "pack_count": len(packs),
        "packs": packs,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_effort_attribution_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_effort_attribution_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / TARGET
    stage = EXT._normalized_stage(source, work_root / "normalized")

    rows = {}
    for level in LEVELS:
        rows[level] = _build(stage, work_root / f"level-{level}", level)

    low = rows[15]
    high = rows[19]
    low_by_hash = {p["sha256"]: p for p in low["packs"]}
    high_by_hash = {p["sha256"]: p for p in high["packs"]}
    same_hashes = set(low_by_hash) == set(high_by_hash)
    if not same_hashes:
        missing_low = sorted(set(high_by_hash) - set(low_by_hash))
        missing_high = sorted(set(low_by_hash) - set(high_by_hash))
        raise RuntimeError(f"raw pack identity drift: only_l19={missing_low[:8]} only_l15={missing_high[:8]}")

    deltas = []
    category_saving = Counter()
    category_l15_bytes = Counter()
    category_l19_bytes = Counter()
    total_pack_saving = 0
    for hh in sorted(low_by_hash):
        a = low_by_hash[hh]
        b = high_by_hash[hh]
        if a["usize"] != b["usize"] or a["crc32"] != b["crc32"]:
            raise RuntimeError(f"raw pack proof drift for {hh}")
        saving = int(a["csize"] - b["csize"])
        total_pack_saving += saving
        labels = a["labels"]
        primary = "+".join(labels)
        category_saving[primary] += saving
        category_l15_bytes[primary] += int(a["csize"])
        category_l19_bytes[primary] += int(b["csize"])
        deltas.append({
            "sha256": hh,
            "usize": a["usize"],
            "l15_csize": a["csize"],
            "l19_csize": b["csize"],
            "saving_bytes": saving,
            "labels": labels,
        })
    deltas.sort(key=lambda row: (-row["saving_bytes"], -row["usize"], row["sha256"]))

    archive_saving = int(low["archive_bytes"] - high["archive_bytes"])
    nonpack_saving = archive_saving - total_pack_saving
    top = deltas[:20]
    top10_saving = sum(max(0, int(row["saving_bytes"])) for row in deltas[:10])
    positive_total = sum(max(0, int(row["saving_bytes"])) for row in deltas)

    category_rows = []
    for name in sorted(category_saving, key=lambda k: (-category_saving[k], k)):
        category_rows.append({
            "category": name,
            "l15_csize": category_l15_bytes[name],
            "l19_csize": category_l19_bytes[name],
            "saving_bytes": category_saving[name],
        })

    invariants = {
        "same_pack_count": low["pack_count"] == high["pack_count"],
        "same_raw_pack_hashes": same_hashes,
        "same_stream_pool_bytes": low["build_stats"]["stream_pool"] == high["build_stats"]["stream_pool"],
        "same_stream_slabs": low["build_stats"]["stream_slabs"] == high["build_stats"]["stream_slabs"],
        "same_special_count": low["build_stats"]["special"] == high["build_stats"]["special"],
        "same_derived_count": low["build_stats"]["derived"] == high["build_stats"]["derived"],
        "same_family_solid_limits": low["build_stats"]["family_solid_limits"] == high["build_stats"]["family_solid_limits"],
    }
    experiment_valid = all(invariants.values())
    if not experiment_valid:
        raise RuntimeError(f"effort attribution structure drift: {invariants!r}")

    return {
        "schema": "cmpct-v030-analytics-l15-l19-pack-attribution-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "levels": list(LEVELS),
        "experiment_valid": True,
        "release_credit": False,
        "rows": {str(k): v for k, v in rows.items()},
        "invariants": invariants,
        "archive_saving_bytes_l15_to_l19": archive_saving,
        "pack_payload_saving_bytes_l15_to_l19": total_pack_saving,
        "nonpack_saving_bytes_l15_to_l19": nonpack_saving,
        "positive_pack_saving_bytes": positive_total,
        "top10_positive_saving_bytes": top10_saving,
        "top20_pack_deltas": top,
        "category_attribution": category_rows,
        "contract": {
            "same_normalized_source": True,
            "same_canonical_filesystem_tax": True,
            "mandatory_strong_verify": True,
            "fixed_levels_only": [15, 19],
            "no_level_sweep": True,
            "no_representation_change": True,
            "no_selector_change": True,
            "no_format_change": True,
        },
        "next_decision": "TARGET_TOP_BYTE_WEIGHT_PACK_MECHANISM",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-effort-attribution-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-effort-attribution.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "archive_saving": result["archive_saving_bytes_l15_to_l19"],
        "top10_positive_saving": result["top10_positive_saving_bytes"],
        "categories": result["category_attribution"][:8],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
