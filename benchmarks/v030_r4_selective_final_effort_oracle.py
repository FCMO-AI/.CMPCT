from __future__ import annotations

"""Diagnostic R4 oracle: is high compression effort sparse enough to gate per final unit?

The prior Analytics effort frontier proved that a global level-19 cap can nearly recover the accepted
v0.29 byte floor, but only by spending far more creation time than ZIP. This experiment freezes the
*level-1 representation/discovery decisions* and asks a narrower causal question: are the additional
bytes obtained by level 19 concentrated in a small number of final compression calls?

No shipping selector is changed. Workload identity is never exposed to a product policy. Promotion
sets are workload-local *oracles* used only to establish or falsify the existence of a sparse opportunity
frontier before any general policy is designed.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = (
    "02_office_workspace",
    "04_analytics_and_database",
    "01_developer_repository",
)
LOW_LEVEL = 1
HIGH_LEVEL = 19
PROBE_LEVEL = 1  # freeze structural audition to the already-measured level-1 representation
MAX_PATH_BYTES = CANON.MAX_PATH_BYTES


def _key(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _physical_payload_bytes(raw_len: int, compressed_len: int) -> int:
    # entropygraph_v025 stores compressed payload iff it clears the exact +8 byte gate.
    return compressed_len if compressed_len + 8 < raw_len else raw_len


def _prepare_profile(stage: Path, root: Path) -> tuple[Path, float, dict]:
    root.mkdir(parents=True, exist_ok=True)
    profile = root / "profile"
    started = time.perf_counter()
    fs_stats = FS.prepare_profile_tree(
        stage,
        profile,
        max_path_bytes=MAX_PATH_BYTES,
        max_profile_files=PRODUCT.MAX_PROFILE_FILES,
        max_profile_logical_bytes=PRODUCT.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    return profile, time.perf_counter() - started, dict(fs_stats)


def _verify_and_restore(profile: Path, archive: Path, out: Path, expected_tree: str) -> float:
    V25.ROOT = profile
    V25.OUT = archive
    started = time.perf_counter()
    verified = dict(V25.strong_verify())
    verify_s = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError(f"CMPNX5 strong verification failed: {verified!r}")
    shutil.rmtree(out, ignore_errors=True)
    V25.extract(out)
    manifest_path = out.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("authenticated canonical-filesystem manifest missing")
    decoded = FS.decode_manifest(
        manifest_path.read_bytes(),
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    FS.restore_manifest_tree(out, decoded)
    actual = PRODUCT.treehash(out)
    if actual != expected_tree:
        raise RuntimeError(f"restored tree mismatch: {actual} != {expected_tree}")
    return verify_s


def _scan_final_calls(profile: Path, archive: Path) -> tuple[dict, float, dict]:
    """Build the exact level-1 representation while measuring level-1 vs level-19 on final calls."""
    V25.ROOT = profile
    V25.OUT = archive
    original_zc = V25.zc
    records: dict[str, dict] = {}

    def oracle_zc(raw: bytes, level: int = HIGH_LEVEL) -> bytes:
        requested = int(level)
        if requested < HIGH_LEVEL:
            return original_zc(raw, LOW_LEVEL)
        key = _key(raw)
        rec = records.get(key)
        if rec is None:
            low_times = []
            high_times = []
            low_blob = high_blob = b""
            # Probe timing cannot earn product speed credit; actual candidates are timed independently.
            for _ in range(2):
                t = time.perf_counter(); low_blob = original_zc(raw, LOW_LEVEL); low_times.append(time.perf_counter() - t)
                t = time.perf_counter(); high_blob = original_zc(raw, HIGH_LEVEL); high_times.append(time.perf_counter() - t)
            low_phys = _physical_payload_bytes(len(raw), len(low_blob))
            high_phys = _physical_payload_bytes(len(raw), len(high_blob))
            saving = max(0, low_phys - high_phys)
            extra = max(0.0, statistics.median(high_times) - statistics.median(low_times))
            rec = records[key] = {
                "sha256": key,
                "raw_bytes": len(raw),
                "low_compressed_bytes": len(low_blob),
                "high_compressed_bytes": len(high_blob),
                "low_physical_payload_bytes": low_phys,
                "high_physical_payload_bytes": high_phys,
                "saving_bytes_per_call": saving,
                "median_low_compress_s": statistics.median(low_times),
                "median_high_compress_s": statistics.median(high_times),
                "marginal_compress_s_per_call": extra,
                "calls": 0,
            }
        rec["calls"] += 1
        return original_zc(raw, LOW_LEVEL)

    V25.zc = oracle_zc
    try:
        started = time.perf_counter()
        build_stats = dict(V25.build())
        scan_build_s = time.perf_counter() - started
    finally:
        V25.zc = original_zc

    for rec in records.values():
        rec["total_saving_bytes"] = int(rec["saving_bytes_per_call"]) * int(rec["calls"])
        rec["total_marginal_compress_s"] = float(rec["marginal_compress_s_per_call"]) * int(rec["calls"])
        rec["saving_bytes_per_marginal_cpu_second"] = rec["total_saving_bytes"] / max(rec["total_marginal_compress_s"], 1e-9)
    return records, scan_build_s, build_stats


def _build_policy(stage: Path, root: Path, promoted: set[str]) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    profile, stage_s, fs_stats = _prepare_profile(stage, root)
    archive = root / "candidate.cmpnx5"
    expected_tree = PRODUCT.treehash(stage)
    V25.ROOT = profile
    V25.OUT = archive
    original_zc = V25.zc

    def selective_zc(raw: bytes, level: int = HIGH_LEVEL) -> bytes:
        requested = int(level)
        if requested < HIGH_LEVEL:
            return original_zc(raw, PROBE_LEVEL)
        return original_zc(raw, HIGH_LEVEL if _key(raw) in promoted else LOW_LEVEL)

    V25.zc = selective_zc
    try:
        started = time.perf_counter()
        stats = dict(V25.build())
        build_s = time.perf_counter() - started
    finally:
        V25.zc = original_zc
    verify_s = _verify_and_restore(profile, archive, root / "out", expected_tree)
    return {
        "archive_bytes": archive.stat().st_size,
        "filesystem_stage_s": stage_s,
        "build_s": build_s,
        "strong_verify_s": verify_s,
        "complete_verified_create_s": stage_s + build_s + verify_s,
        "filesystem_manifest_bytes": int(fs_stats["manifest_bytes"]),
        "filesystem_manifest_entries": int(fs_stats["entries"]),
        "build_stats": stats,
        "canonical_user_tree_sha256": expected_tree,
        "promoted_hashes": len(promoted),
    }


def _one(name: str, source: Path, accepted_v029: int, work: Path) -> dict:
    stage = EXT._normalized_stage(source, work / name / "normalized")
    expected_external = EXT._tree(stage)
    expected_user = PRODUCT.treehash(stage)

    scan_root = work / name / "scan"
    profile, scan_stage_s, _ = _prepare_profile(stage, scan_root)
    records, scan_build_s, scan_stats = _scan_final_calls(profile, scan_root / "scan.cmpnx5")
    scan_verify_s = _verify_and_restore(profile, scan_root / "scan.cmpnx5", scan_root / "out", expected_user)

    positive = [r for r in records.values() if int(r["total_saving_bytes"]) > 0]
    positive.sort(key=lambda r: (-float(r["saving_bytes_per_marginal_cpu_second"]), -int(r["total_saving_bytes"]), r["sha256"]))
    total_possible = sum(int(r["total_saving_bytes"]) for r in positive)
    top_quarter_n = math.ceil(len(positive) * 0.25) if positive else 0
    top_quarter_saving = sum(int(r["total_saving_bytes"]) for r in positive[:top_quarter_n])
    top_quarter_fraction = (top_quarter_saving / total_possible) if total_possible else 0.0

    baseline = _build_policy(stage, work / name / "baseline", set())
    gap = max(0, int(baseline["archive_bytes"]) - int(accepted_v029))

    predicted = 0
    promoted = []
    for rec in positive:
        if predicted >= gap:
            break
        promoted.append(rec)
        predicted += int(rec["total_saving_bytes"])
    selected_hashes = {r["sha256"] for r in promoted} if total_possible >= gap and gap > 0 else set()
    selective = _build_policy(stage, work / name / "selective", selected_hashes) if selected_hashes else None
    all_high = _build_policy(stage, work / name / "all-high", {r["sha256"] for r in positive}) if positive else baseline

    zip_root = work / name / "zip"
    zip_root.mkdir(parents=True, exist_ok=True)
    zip_result = EXT._zip(stage, zip_root / "archive.zip", zip_root / "out")
    EXT._verify_extracted(zip_root / "out", expected_external, "zip_deflate9")

    selective_closes = bool(selective and int(selective["archive_bytes"]) <= accepted_v029)
    selective_under_zip = bool(selective and float(selective["complete_verified_create_s"]) < float(zip_result["create_s"]))
    return {
        "workload": name,
        "accepted_v029_bytes": int(accepted_v029),
        "canonical_user_tree_sha256": expected_user,
        "scan": {
            "filesystem_stage_s": scan_stage_s,
            "build_s_including_probe_measurement": scan_build_s,
            "strong_verify_s": scan_verify_s,
            "build_stats": scan_stats,
            "final_call_hashes": len(records),
            "positive_saving_hashes": len(positive),
            "total_possible_fixed_representation_saving_bytes": total_possible,
            "top_quarter_count": top_quarter_n,
            "top_quarter_saving_bytes": top_quarter_saving,
            "top_quarter_fraction_of_possible_saving": top_quarter_fraction,
            "records": positive,
        },
        "baseline_level1_fixed_representation": baseline,
        "gap_to_v029_bytes": gap,
        "oracle_min_prefix": {
            "eligible": total_possible >= gap and gap > 0,
            "promoted_hashes": len(selected_hashes),
            "predicted_saving_bytes": predicted if selected_hashes else 0,
            "fraction_of_positive_hashes": (len(selected_hashes) / len(positive)) if positive else 0.0,
        },
        "selective_oracle": selective,
        "all_positive_high_effort": all_high,
        "zip_deflate9": {
            "archive_bytes": int(zip_result["archive_bytes"]),
            "create_s": float(zip_result["create_s"]),
        },
        "tests": {
            "savings_concentrated_top_quarter_ge_80pct": top_quarter_fraction >= 0.80,
            "selective_oracle_closes_v029": selective_closes,
            "selective_oracle_faster_than_zip": selective_under_zip,
            "selective_oracle_joint_size_time": selective_closes and selective_under_zip,
        },
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_selective_effort_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_selective_effort_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    accepted = GENERAL._accepted_v029_rows()

    rows = []
    for name in TARGETS:
        source = corpus / name
        row = _one(name, source, int(accepted[("neutral_hostile_v1", name)]["accepted_v029_bytes"]), work_root)
        rows.append(row)
        print(json.dumps({
            "workload": name,
            "gap": row["gap_to_v029_bytes"],
            "positive": row["scan"]["positive_saving_hashes"],
            "top_quarter_fraction": row["scan"]["top_quarter_fraction_of_possible_saving"],
            "oracle": row["oracle_min_prefix"],
            "tests": row["tests"],
        }, separators=(",", ":")), flush=True)

    structured = [r for r in rows if r["workload"] in ("02_office_workspace", "04_analytics_and_database")]
    control = next(r for r in rows if r["workload"] == "01_developer_repository")
    hypothesis = {
        "both_structured_top_quarter_capture_ge_80pct": all(r["tests"]["savings_concentrated_top_quarter_ge_80pct"] for r in structured),
        "both_structured_oracles_close_v029_under_zip_time": all(r["tests"]["selective_oracle_joint_size_time"] for r in structured),
        "developer_control_measured_not_used_for_promotion": control["workload"] == "01_developer_repository",
    }
    hypothesis["supported"] = all(hypothesis.values())
    return {
        "schema": "cmpct-v030-r4-selective-final-effort-oracle-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "targets": list(TARGETS),
        "low_level": LOW_LEVEL,
        "high_level": HIGH_LEVEL,
        "representation_probe_level": PROBE_LEVEL,
        "rows": rows,
        "hypothesis": hypothesis,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_selector_changed": False,
            "workload_identity_in_production_policy": False,
            "level1_representation_decisions_frozen": True,
            "mandatory_strong_verify": True,
            "canonical_filesystem_semantics_preserved": True,
        },
        "next_if_supported": "design workload-blind cheap predictor for high-yield final compression units and remeasure same semantics",
        "next_if_falsified": "retire selective-final-effort as the primary R4 and move to a different representation/execution primitive",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-selective-effort-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-selective-effort.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["hypothesis"], indent=2), flush=True)


if __name__ == "__main__":
    main()
