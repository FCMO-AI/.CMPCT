from __future__ import annotations

"""R4 Analytics byte-plane transform oracle.

The exact v0.29-effort frontier retired global compression-effort tuning: level 19 nearly
reaches the accepted v0.29 byte floor but misses it by 531 B while taking 8.79 s versus
ZIP's 1.36 s on the same normalized tree. This oracle therefore changes representation,
not level.

Hypothesis: a fixed reversible 4-byte byte-plane transpose exposes low-order / exponent /
field-position correlation in large numeric and database-like buffers so Zstd-1 can recover
v0.29-class density without paying high-level search cost. Every V25 Zstd call keeps the
ordinary level-1 result as a fallback and auditions exactly one width-4 transform. The
transform is admitted only when its fully framed bytes are strictly smaller. No workload,
path, extension, benchmark identity, threshold sweep, or level sweep enters selection.

This is an oracle, not a canonical format proposal. Transformed payloads carry a research
marker understood only by the monkey-patched research reader in this lane. A red result
retires this direct byte-plane mechanism; a green result merely earns a productization gate
with explicit format/auth/locality/native work.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
ROUNDS = 3
WIDTH = 4
MAGIC = b"BP4\x00\x01"


def _shuffle4(raw: bytes) -> bytes:
    q = len(raw) // WIDTH
    main = raw[: q * WIDTH]
    return b"".join(main[i::WIDTH] for i in range(WIDTH)) + raw[q * WIDTH :]


def _unshuffle4(shuffled: bytes) -> bytes:
    q = len(shuffled) // WIDTH
    main_n = q * WIDTH
    out = bytearray(len(shuffled))
    main = shuffled[:main_n]
    for i in range(WIDTH):
        out[i:main_n:WIDTH] = main[i * q : (i + 1) * q]
    out[main_n:] = shuffled[main_n:]
    return bytes(out)


def _candidate_once(stage: Path, root: Path) -> dict:
    original_zc = V25.zc
    original_zd = V25.zd
    stats = {
        "zc_calls": 0,
        "auditioned_calls": 0,
        "selected_calls": 0,
        "auditioned_raw_bytes": 0,
        "selected_raw_bytes": 0,
        "direct_payload_bytes_for_selected": 0,
        "selected_payload_bytes": 0,
    }

    def plane_zc(raw: bytes, level: int = 19) -> bytes:
        stats["zc_calls"] += 1
        direct = original_zc(raw, min(int(level), 1))
        if len(raw) < WIDTH:
            return direct
        stats["auditioned_calls"] += 1
        stats["auditioned_raw_bytes"] += len(raw)
        transformed = _shuffle4(raw)
        encoded = original_zc(transformed, min(int(level), 1))
        framed = MAGIC + encoded
        if len(framed) < len(direct):
            stats["selected_calls"] += 1
            stats["selected_raw_bytes"] += len(raw)
            stats["direct_payload_bytes_for_selected"] += len(direct)
            stats["selected_payload_bytes"] += len(framed)
            return framed
        return direct

    def plane_zd(payload: bytes, usize: int) -> bytes:
        if payload.startswith(MAGIC):
            shuffled = original_zd(payload[len(MAGIC) :], usize)
            raw = _unshuffle4(shuffled)
            if len(raw) != usize:
                raise RuntimeError("byte-plane inverse length mismatch")
            return raw
        return original_zd(payload, usize)

    V25.zc = plane_zc
    V25.zd = plane_zd
    original_cap = CANON.LEVEL_CAP
    CANON.LEVEL_CAP = 1
    try:
        result = CANON._canonical_v25(stage, root)
    finally:
        CANON.LEVEL_CAP = original_cap
        V25.zc = original_zc
        V25.zd = original_zd

    result = dict(result)
    result["byteplane"] = dict(stats)
    result["byteplane"]["payload_saving_bytes"] = (
        stats["direct_payload_bytes_for_selected"] - stats["selected_payload_bytes"]
    )
    return result


def _baseline_once(stage: Path, root: Path) -> dict:
    original_cap = CANON.LEVEL_CAP
    CANON.LEVEL_CAP = 1
    try:
        return dict(CANON._canonical_v25(stage, root))
    finally:
        CANON.LEVEL_CAP = original_cap


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_byteplane4_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_byteplane4_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / TARGET
    accepted = int(GENERAL._accepted_v029_rows()[("neutral_hostile_v1", TARGET)]["accepted_v029_bytes"])

    stage = EXT._normalized_stage(source, work_root / "normalized")
    expected_external_tree = EXT._tree(stage)
    expected_user_tree = PRODUCT.treehash(stage)

    samples = {"baseline": [], "candidate": [], "zip": [], "zstd19": []}
    sizes = {name: set() for name in samples}
    candidate_stats = []

    for rep in range(ROUNDS):
        order = ("baseline", "candidate", "zip", "zstd19")
        shift = rep % len(order)
        order = order[shift:] + order[:shift]
        for engine in order:
            root = work_root / "rounds" / f"r{rep}-{engine}"
            root.mkdir(parents=True, exist_ok=True)
            if engine == "baseline":
                result = _baseline_once(stage, root)
                if result["canonical_user_tree_sha256"] != expected_user_tree:
                    raise RuntimeError("baseline canonical user-tree drift")
                samples[engine].append(float(result["complete_verified_create_s"]))
                sizes[engine].add(int(result["archive_bytes"]))
            elif engine == "candidate":
                result = _candidate_once(stage, root)
                if result["canonical_user_tree_sha256"] != expected_user_tree:
                    raise RuntimeError("candidate canonical user-tree drift")
                samples[engine].append(float(result["complete_verified_create_s"]))
                sizes[engine].add(int(result["archive_bytes"]))
                candidate_stats.append(result["byteplane"])
            elif engine == "zip":
                result = EXT._zip(stage, root / "archive.zip", root / "out")
                EXT._verify_extracted(root / "out", expected_external_tree, "zip_deflate9")
                samples[engine].append(float(result["create_s"]))
                sizes[engine].add(int(result["archive_bytes"]))
            else:
                result = EXT._tar_zstd(stage, root / "archive.tar.zst", root / "out", root)
                if not result.get("available"):
                    raise RuntimeError(f"Zstd-19 unavailable: {result!r}")
                EXT._verify_extracted(root / "out", expected_external_tree, "tar_zstd19_solid")
                samples[engine].append(float(result["create_s"]))
                sizes[engine].add(int(result["archive_bytes"]))

    if any(len(v) != 1 for v in sizes.values()):
        raise RuntimeError(f"archive size nondeterminism: {sizes!r}")
    byte_values = {k: next(iter(v)) for k, v in sizes.items()}
    medians = {k: statistics.median(v) for k, v in samples.items()}

    strict = {
        "smaller_than_direct_level1": byte_values["candidate"] < byte_values["baseline"],
        "no_regression_vs_v029": byte_values["candidate"] <= accepted,
        "smaller_than_zip": byte_values["candidate"] < byte_values["zip"],
        "smaller_than_zstd19": byte_values["candidate"] < byte_values["zstd19"],
        "faster_than_zip": medians["candidate"] < medians["zip"],
        "faster_than_zstd19": medians["candidate"] < medians["zstd19"],
    }
    strict["oracle_passed"] = all(strict.values())

    stable_stats = {
        key: [int(row[key]) for row in candidate_stats]
        for key in candidate_stats[0]
    }
    return {
        "schema": "cmpct-v030-analytics-byteplane4-oracle-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "rounds": ROUNDS,
        "width": WIDTH,
        "accepted_v029_bytes": accepted,
        "bytes": byte_values,
        "median_complete_verified_create_s": medians,
        "raw_complete_verified_create_s": samples,
        "candidate_byteplane_stats": stable_stats,
        "saving_vs_direct_level1_bytes": byte_values["baseline"] - byte_values["candidate"],
        "saving_vs_v029_bytes": accepted - byte_values["candidate"],
        "strict": strict,
        "contract": {
            "fixed_transform_width": 4,
            "direct_level1_fallback_per_zstd_call": True,
            "transform_admission_is_exact_framed_byte_cost": True,
            "canonical_filesystem_tax_inside_candidate_timing": True,
            "mandatory_strong_verify_inside_candidate_timing": True,
            "fresh_comparators_same_normalized_tree": True,
            "production_selector_changed": False,
            "benchmark_identity_in_production_policy": False,
            "canonical_format_changed": False,
            "release_credit": False,
        },
        "experiment_valid": True,
        "release_credit": False,
        "next_decision": (
            "PRODUCTIZE_TRANSFORM" if strict["oracle_passed"] else "RETIRE_DIRECT_BYTEPLANE4"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-byteplane4-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-byteplane4.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"strict": result["strict"], "next_decision": result["next_decision"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
