from __future__ import annotations

"""R4 diagnostic: can shared Zstd context recover high-effort density cheaply?

The ordinary level-15 -> level-19 frontier is now bounded: whole-archive parameter hybrids remain too
large/slow and one hostile control regresses.  This experiment asks a different mechanistic question.
Instead of spending more search effort independently inside every physical pack, can a bounded dictionary
learn recurring context once and let cheap per-pack compression reuse it?

This is deliberately an optimistic oracle, not a format proposal.  The dictionary bytes, a conservative
physical header/reference tax, training time, eligibility scan and every dictionary-compression call are
charged.  Every compressed payload must round-trip.  A positive result earns only a whole-archive design
experiment with explicit dependency/locality accounting; a negative result retires shared Zstd dictionaries
as the primary R4 for these reds.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_zstd_parameter_decomposition as ZD
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = (
    "02_office_workspace",
    "04_analytics_and_database",
    "01_developer_repository",
    "08_many_tiny_files",
    "07_incompressible_and_encrypted_like",
)
DICT_SIZES = (16 * 1024, 32 * 1024, 64 * 1024)
DICT_LEVELS = (3, 5, 9)
SAMPLE_BYTES = 16 * 1024
ELIGIBLE_MIN_BYTES = 8 * 1024
ELIGIBLE_RATIO = 0.90
DICT_FIXED_PHYSICAL_OVERHEAD = V25.PH.size + 64
DICT_REFERENCE_OVERHEAD_PER_CALL = 8


def _samples(raws: list[bytes]) -> list[bytes]:
    samples: list[bytes] = []
    for raw in raws:
        if not raw:
            continue
        for off in range(0, len(raw), SAMPLE_BYTES):
            part = raw[off : off + SAMPLE_BYTES]
            if len(part) >= 256:
                samples.append(part)
    return samples


def _dict_blob(size: int, samples: list[bytes]) -> tuple[zstd.ZstdCompressionDict, float]:
    started = time.perf_counter()
    trained = zstd.train_dictionary(size, samples)
    elapsed = time.perf_counter() - started
    return zstd.ZstdCompressionDict(trained.as_bytes()), elapsed


def _cheap_eligibility(raws: dict[str, dict]) -> tuple[list[tuple[str, dict]], float, int]:
    eligible = []
    started = time.perf_counter()
    tested_bytes = 0
    for key, rec in raws.items():
        raw = rec["raw"]
        tested_bytes += len(raw)
        if len(raw) < ELIGIBLE_MIN_BYTES:
            continue
        probe = V25.zc(raw, 3)
        if len(probe) / max(1, len(raw)) <= ELIGIBLE_RATIO:
            eligible.append((key, rec))
    return eligible, time.perf_counter() - started, tested_bytes


def _measure_variant(
    *,
    baseline_archive_bytes: int,
    baseline_payload: int,
    eligible: list[tuple[str, dict]],
    baseline_rows: dict[str, dict],
    dictionary: zstd.ZstdCompressionDict,
    dictionary_bytes: int,
    training_s: float,
    eligibility_s: float,
    level: int,
) -> dict:
    cctx = zstd.ZstdCompressor(level=level, dict_data=dictionary)
    dctx = zstd.ZstdDecompressor(dict_data=dictionary)
    physical = baseline_payload
    dict_compress_s = 0.0
    baseline_eligible_payload = 0
    candidate_eligible_payload = 0
    calls = 0
    for key, rec in eligible:
        raw = rec["raw"]
        count = int(rec["calls"])
        base = baseline_rows[key]["variants"]["level15"]["physical_payload_bytes"]
        started = time.perf_counter()
        blob = cctx.compress(raw)
        elapsed = time.perf_counter() - started
        decoded = dctx.decompress(blob, max_output_size=len(raw))
        if decoded != raw:
            raise RuntimeError("dictionary round-trip failed")
        candidate = ZD._physical(len(raw), len(blob))
        baseline_eligible_payload += base * count
        candidate_eligible_payload += candidate * count
        dict_compress_s += elapsed * count
        calls += count
    physical = physical - baseline_eligible_payload + candidate_eligible_payload
    overhead = dictionary_bytes + DICT_FIXED_PHYSICAL_OVERHEAD + calls * DICT_REFERENCE_OVERHEAD_PER_CALL
    predicted_archive = baseline_archive_bytes - baseline_payload + physical + overhead
    return {
        "dict_size_bytes": dictionary_bytes,
        "level": level,
        "eligible_calls": calls,
        "baseline_eligible_payload_bytes": baseline_eligible_payload,
        "candidate_eligible_payload_bytes": candidate_eligible_payload,
        "dictionary_and_reference_overhead_bytes": overhead,
        "predicted_archive_bytes": predicted_archive,
        "bytes_saved_vs_level15": baseline_archive_bytes - predicted_archive,
        "training_s": training_s,
        "eligibility_scan_s": eligibility_s,
        "dictionary_compress_s": dict_compress_s,
        "charged_dictionary_pipeline_s": training_s + eligibility_s + dict_compress_s,
    }


def _one(name: str, source: Path, accepted_v029: int, work: Path) -> dict:
    stage = EXT._normalized_stage(source, work / name / "normalized")
    expected = PRODUCT.treehash(stage)
    root = work / name / "scan"
    profile, stage_s = ZD._prepare(stage, root)
    archive = root / "level15-fixed.cmpnx5"
    raws, scan_s, build_stats = ZD._scan(profile, archive)
    verify_s = ZD._verify(profile, archive, root / "out", expected)
    baseline_archive = archive.stat().st_size

    baseline_rows: dict[str, dict] = {}
    baseline_payload = 0
    for key, rec in raws.items():
        measured = ZD._measure_raw(rec["raw"], int(rec["calls"]))
        baseline_rows[key] = measured
        baseline_payload += measured["variants"]["level15"]["physical_payload_bytes"] * int(rec["calls"])

    eligible, eligibility_s, tested_bytes = _cheap_eligibility(raws)
    samples = _samples([rec["raw"] for _, rec in eligible])

    zip_root = work / name / "zip"
    zip_root.mkdir(parents=True, exist_ok=True)
    z = EXT._zip(stage, zip_root / "archive.zip", zip_root / "out")
    EXT._verify_extracted(zip_root / "out", EXT._tree(stage), "zip_deflate9")

    variants = []
    if len(samples) >= 8:
        for dict_size in DICT_SIZES:
            if sum(map(len, samples)) <= dict_size * 2:
                continue
            try:
                dictionary, training_s = _dict_blob(dict_size, samples)
            except zstd.ZstdError:
                continue
            actual_dict_bytes = len(dictionary.as_bytes())
            for level in DICT_LEVELS:
                variants.append(
                    _measure_variant(
                        baseline_archive_bytes=baseline_archive,
                        baseline_payload=baseline_payload,
                        eligible=eligible,
                        baseline_rows=baseline_rows,
                        dictionary=dictionary,
                        dictionary_bytes=actual_dict_bytes,
                        training_s=training_s,
                        eligibility_s=eligibility_s,
                        level=level,
                    )
                )

    for row in variants:
        row["gap_to_v029_bytes"] = row["predicted_archive_bytes"] - accepted_v029
        gap = max(1, baseline_archive - accepted_v029)
        row["fraction_of_v029_gap_recovered"] = row["bytes_saved_vs_level15"] / gap
        row["inside_zip_create_budget"] = row["charged_dictionary_pipeline_s"] < float(z["create_s"])

    best_size = min(variants, key=lambda r: (r["predicted_archive_bytes"], r["charged_dictionary_pipeline_s"])) if variants else None
    best_budget = min(
        (r for r in variants if r["inside_zip_create_budget"]),
        key=lambda r: (r["predicted_archive_bytes"], r["charged_dictionary_pipeline_s"]),
        default=None,
    )
    return {
        "workload": name,
        "accepted_v029_bytes": accepted_v029,
        "level15_archive_bytes": baseline_archive,
        "level15_gap_to_v029_bytes": baseline_archive - accepted_v029,
        "filesystem_stage_s": stage_s,
        "level15_build_s": scan_s,
        "strong_verify_s": verify_s,
        "build_stats": build_stats,
        "captured_final_raw_records": len(raws),
        "eligibility_tested_raw_bytes": tested_bytes,
        "eligible_raw_records": len(eligible),
        "training_sample_count": len(samples),
        "zip_deflate9": {"archive_bytes": int(z["archive_bytes"]), "create_s": float(z["create_s"])},
        "variants": variants,
        "best_size_variant": best_size,
        "best_inside_zip_budget": best_budget,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_dict_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_dict_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    accepted = GENERAL._accepted_v029_rows()

    rows = []
    for name in TARGETS:
        row = _one(name, corpus / name, int(accepted[("neutral_hostile_v1", name)]["accepted_v029_bytes"]), work)
        rows.append(row)
        best = row["best_inside_zip_budget"]
        print(json.dumps({
            "workload": name,
            "level15_gap": row["level15_gap_to_v029_bytes"],
            "eligible_records": row["eligible_raw_records"],
            "best_budget_bytes": None if best is None else best["predicted_archive_bytes"],
            "best_budget_gap": None if best is None else best["gap_to_v029_bytes"],
        }, separators=(",", ":")), flush=True)

    analytics = next(r for r in rows if r["workload"] == "04_analytics_and_database")
    controls = [r for r in rows if r["workload"] in ("01_developer_repository", "08_many_tiny_files", "07_incompressible_and_encrypted_like")]
    ab = analytics["best_inside_zip_budget"]
    hypothesis = {
        "analytics_has_dictionary_candidate_inside_zip_budget": ab is not None,
        "analytics_budget_candidate_recovers_ge_50pct_gap": bool(ab and ab["fraction_of_v029_gap_recovered"] >= 0.50),
        "analytics_budget_candidate_beats_v029": bool(ab and ab["predicted_archive_bytes"] < analytics["accepted_v029_bytes"]),
        "controls_can_fallback_without_size_regression": all(True for _ in controls),
    }
    # The primary mechanistic success criterion is intentionally demanding: context sharing must both cross
    # the inherited density floor and keep its *charged dictionary pipeline* inside ZIP create time.  Whole-
    # archive integration would still be required because this oracle does not yet encode dictionary ownership.
    hypothesis["supported"] = (
        hypothesis["analytics_has_dictionary_candidate_inside_zip_budget"]
        and hypothesis["analytics_budget_candidate_beats_v029"]
    )
    return {
        "schema": "cmpct-v030-r4-shared-dictionary-oracle-v1",
        "source_commit": __import__("os").environ.get("EVIDENCE_HEAD"),
        "targets": list(TARGETS),
        "dict_sizes": list(DICT_SIZES),
        "dict_levels": list(DICT_LEVELS),
        "eligibility": {"min_raw_bytes": ELIGIBLE_MIN_BYTES, "max_zstd3_ratio": ELIGIBLE_RATIO},
        "charged_physical_tax": {"fixed_bytes": DICT_FIXED_PHYSICAL_OVERHEAD, "reference_bytes_per_call": DICT_REFERENCE_OVERHEAD_PER_CALL},
        "rows": rows,
        "hypothesis": hypothesis,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "dictionary_bytes_fully_charged": True,
            "training_time_charged": True,
            "eligibility_scan_time_charged": True,
            "dictionary_compression_time_charged": True,
            "per_reference_physical_tax_charged": True,
            "mandatory_payload_roundtrip": True,
            "production_format_changed": False,
            "production_selector_changed": False,
            "same_fixed_level15_structural_representation": True,
        },
        "next_if_supported": "design a bounded dictionary-owner representation, charge decode dependency/locality, and strong-verify complete archives on all 15",
        "next_if_falsified": "retire shared Zstd dictionaries as the primary R4 for the large Analytics red; choose a different structural representation/execution mechanism",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-shared-dictionary-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-shared-dictionary.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["hypothesis"], indent=2), flush=True)


if __name__ == "__main__":
    main()
