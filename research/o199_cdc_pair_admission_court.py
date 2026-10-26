#!/usr/bin/env python3
"""O199: prospectively preregistered bounded content-only CDC pair-admission falsifier.
Scientific proxy only, not CMPCT archive/Reader product proof or a pair-discovery implementation.
Frozen conditions: docs/v031-research/2026-10-26-o199-prospective-cdc-pair-admission-prereg.md.
"""
from __future__ import annotations
import hashlib, json, platform, statistics, sys, tempfile, time, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
from o197_native_cdc_mutation_court import authenticate_and_compile, SOURCE_BLOB
from o198_cdc_codec_aware_oracle import corpus, measure, SIZE

SEEDS = (711, 712, 713)
FAMILIES = ("entropy", "repeat", "mixed")
POSITIONS = (1, SIZE // 3, 2 * SIZE // 3, 95 * SIZE // 100)
MUTATIONS = ("overwrite", "shift1", "shift256")
MODES = ("fixed256", "fixed512", "fixed1024", "native")


def detector(base: bytes, variant: bytes) -> dict:
    """Prospective decision. No result labels, known mutation flags or file names enter."""
    start = time.perf_counter_ns()
    c0 = time.process_time_ns()
    n = min(len(base), len(variant))
    offsets = []
    searched = 0
    for quarter in (1, 2, 3):
        pos = min(n * quarter // 4, len(base) - 64)
        if pos < 0:
            offsets.append(None)
            continue
        anchor = base[pos:pos + 64]
        lo, hi = max(0, pos - 4096), min(len(variant), pos + 4096 + 64)
        searched += hi - lo
        at = variant.find(anchor, lo, hi)
        offsets.append(None if at < 0 else at - pos)
    valid = [x for x in offsets if x is not None]
    shifted = [x for x in valid if x != 0]
    found_shift = len(valid) >= 2 and bool(shifted) and len(set(shifted)) == 1
    raw_sample = compressed_sample = 0
    for i in range(12):
        pos = int((i + 0.5) * len(base) / 12) - 2048
        pos = min(max(pos, 0), len(base) - 4096)
        sample = base[pos:pos + 4096]
        raw_sample += len(sample)
        compressed_sample += len(zlib.compress(sample, 6))
    ratio = compressed_sample / raw_sample if raw_sample else 0.0
    return {
        "admit": found_shift and ratio >= 0.90,
        "anchor_displacements": offsets, "bounded_shift_detected": found_shift,
        "sample_zlib_ratio": round(ratio, 8),
        "sampled_bytes": raw_sample, "anchor_bytes": 192,
        "lookup_window_bytes_upper_bound": searched,
        "detector_cpu_ms_single": round((time.process_time_ns() - c0) / 1e6, 6),
        "detector_wall_ms_single": round((time.perf_counter_ns() - start) / 1e6, 6),
    }


def mutate(base: bytes, pos: int, kind: str) -> bytes:
    if kind == "overwrite":
        b = bytearray(base)
        b[pos] ^= 0x5a
        return bytes(b)
    amount = 1 if kind == "shift1" else 256
    return base[:pos] + b"Q" * amount + base[pos:-amount]


def main():
    start = time.time()
    with tempfile.TemporaryDirectory(prefix="cmpct-o199-") as tmp:
        lib, compiler = authenticate_and_compile(ROOT, Path(tmp) / "cdc.so")
        rows = []
        for family in FAMILIES:
            for seed in SEEDS:
                base = corpus(family, seed)
                assert len(base) == SIZE
                for pos in POSITIONS:
                    for mutation in MUTATIONS:
                        other = mutate(base, pos, mutation)
                        assert len(other) == len(base)
                        # Observation and choice precede ANY full candidate costing.
                        detect = detector(base, other)
                        results = {m: measure(base, other, m, lib) for m in MODES}
                        fixed = min(MODES[:-1],
                                    key=lambda m: results[m]["charged_storage_proxy_bytes"])
                        fixed_bytes = results[fixed]["charged_storage_proxy_bytes"]
                        native_bytes = results["native"]["charged_storage_proxy_bytes"]
                        rows.append({
                            "family": family, "seed": seed, "position": pos,
                            "mutation": mutation, "base_sha256": hashlib.sha256(base).hexdigest(),
                            "variant_sha256": hashlib.sha256(other).hexdigest(),
                            "detector": detect, "best_fixed_hindsight": fixed,
                            "best_fixed_proxy_bytes": fixed_bytes,
                            "gated_proxy_bytes": native_bytes if detect["admit"] else fixed_bytes,
                            "native_saving_bytes_vs_best_fixed": fixed_bytes - native_bytes,
                            "native_saving_percent_vs_best_fixed":
                                round(100 * (fixed_bytes-native_bytes)/fixed_bytes, 6),
                            "modes": results,
                        })
        unrelated = []
        for family in FAMILIES:
            for seed in SEEDS:
                base, stranger = corpus(family, seed), corpus(family, seed + 1000)
                unrelated.append({
                    "family": family, "seed": seed, "detector": detector(base, stranger),
                    "base_sha256": hashlib.sha256(base).hexdigest(),
                    "stranger_sha256": hashlib.sha256(stranger).hexdigest(),
                })

    assert len(rows) == 108 and len(unrelated) == 9
    assert all(x["modes"][m]["exact_reassembly"] for x in rows for m in MODES)
    nonshift_fp = [x for x in rows if x["mutation"] == "overwrite" and x["detector"]["admit"]]
    unrelated_fp = [x for x in unrelated if x["detector"]["admit"]]
    eligible = [x for x in rows if x["family"] == "entropy"
                and x["mutation"].startswith("shift") and x["position"] != POSITIONS[-1]]
    admitted = [x for x in eligible if x["detector"]["admit"]]
    losses = [x for x in rows if x["detector"]["admit"]
              and x["native_saving_bytes_vs_best_fixed"] < 0]
    supported = not nonshift_fp and not unrelated_fp and len(admitted) >= len(eligible)/2 and not losses
    recap = {
        "nonshift_false_positives": len(nonshift_fp),
        "unrelated_false_positives": len(unrelated_fp),
        "eligible_entropy_shift": len(eligible),
        "admitted_entropy_shift": len(admitted),
        "admitted_entropy_shift_recall": round(len(admitted)/len(eligible), 6),
        "admitted_native_losses": len(losses),
        "total_gated_proxy_minus_best_fixed_bytes":
            sum(x["gated_proxy_bytes"] - x["best_fixed_proxy_bytes"] for x in rows),
        "total_unconditional_native_minus_best_fixed_bytes":
            sum(x["modes"]["native"]["charged_storage_proxy_bytes"] -
                x["best_fixed_proxy_bytes"] for x in rows),
        "detector_cpu_ms_single_sum":
            round(sum(x["detector"]["detector_cpu_ms_single"] for x in rows), 3),
        "detector_wall_ms_single_sum":
            round(sum(x["detector"]["detector_wall_ms_single"] for x in rows), 3),
        "detector_sampled_bytes_sum":
            sum(x["detector"]["sampled_bytes"] for x in rows),
        "detector_lookup_upper_bound_bytes_sum":
            sum(x["detector"]["lookup_window_bytes_upper_bound"] for x in rows),
        "decision": "SUPPORTED_SCOPED_PAIR_SIGNAL_NOT_PRODUCT" if supported else "FALSIFIED_OR_NARROWED",
    }
    by_family = {}
    for family in FAMILIES:
        for mutation in MUTATIONS:
            group = [x for x in rows if x["family"] == family and x["mutation"] == mutation]
            wins = [x for x in group if x["detector"]["admit"]]
            by_family[f"{family}/{mutation}"] = {
                "count": len(group), "admitted": len(wins),
                "admitted_native_wins_vs_strongest_fixed":
                    sum(x["native_saving_bytes_vs_best_fixed"] > 0 for x in wins),
                "admitted_native_losses_vs_strongest_fixed":
                    sum(x["native_saving_bytes_vs_best_fixed"] < 0 for x in wins),
                "admitted_median_saving_percent":
                    round(statistics.median(x["native_saving_percent_vs_best_fixed"]
                                            for x in wins), 6) if wins else None,
            }
    result = {
        "schema": "cmpct-o199-preregistered-prospective-pair-detector-v1",
        "source_native_git_blob": SOURCE_BLOB,
        "base_o198_source": "891b818c1135ccc0b938d5bce4b52c6cae56b080",
        "compiler": compiler, "host": platform.platform(),
        "seeds": SEEDS, "families": FAMILIES, "positions": POSITIONS, "mutations": MUTATIONS,
        "detector_probes": {"anchor_bytes_each": 64, "anchor_locations": [1,2,3],
                            "search_radius": 4096, "samples": 12,
                            "sample_bytes_each": 4096, "zlib_level": 6, "min_ratio": 0.90},
        "scope": "KNOWN SINGLE CANDIDATE PAIR; NO GENERAL FILESYSTEM PAIR DISCOVERY",
        "proxy_charge": "zlib6 unique chunks +64B per physical record +32B per logical ref",
        "controls": "Shipping fixed256 and hindsight gifted best fixed256/512/1024.",
        "omissions": "Real CMPCT archives, pair-index, N^2 cost, total CPU/RSS/temp, selective read, portability",
        "wall_s": round(time.time()-start, 3),
        "recap": recap, "by_family": by_family, "observations": rows, "unrelated": unrelated,
    }
    out = ROOT / "o199-evidence"
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps(result, indent=2)+"\n")
    print("O199_RECAP="+json.dumps(recap, sort_keys=True))
    print("O199_RECONSTRUCTION_CHECK=PASS")
    print("O199_PRODUCT_GATE=UNMEASURED")


if __name__ == "__main__":
    main()
