#!/usr/bin/env python3
"""O8c frozen same-path Builder policy-versus-no-PACK cost court."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import sys
import tempfile
import time

from cmpct.builder import Builder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import native_pack_heldout_o8 as o8
from native_pack_heldout_o8b import FAMILIES, transformed

REPS = 4
MICRO_PACK_ENV = "CMPCT_MICRO_PACK_MAX_FILE"


def full_cpu_ms() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (own.ru_utime + own.ru_stime + child.ru_utime + child.ru_stime) * 1000.0


def build_controlled(source: Path, archive: Path, policy: str) -> dict:
    assert policy in ("normal", "no_pack")
    previous = os.environ.get(MICRO_PACK_ENV)
    try:
        if policy == "no_pack":
            os.environ[MICRO_PACK_ENV] = "0"
        else:
            os.environ.pop(MICRO_PACK_ENV, None)
        cpu0 = full_cpu_ms()
        start = time.perf_counter_ns()
        builder = Builder(source, workers=1, reproducible=True)
        if policy == "no_pack":
            assert builder.micro_pack_max_file == 0
        else:
            assert builder.micro_pack_max_file > 0
        builder.build(archive)
        elapsed_ms = (time.perf_counter_ns() - start) / 1e6
        cpu_ms = full_cpu_ms() - cpu0
    finally:
        if previous is None:
            os.environ.pop(MICRO_PACK_ENV, None)
        else:
            os.environ[MICRO_PACK_ENV] = previous
    return dict(
        policy=policy,
        archive_bytes=archive.stat().st_size,
        archive_sha256=o8.hash_file(archive),
        create_wall_ms=elapsed_ms,
        create_cpu_ms=cpu_ms,
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tests/native_pack_samepath_o8c.py C_BINARY RECEIPT")
    binary = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    assert binary.is_file()
    report = {
        "schema": "cmpct-native-micropack-samepath-o8c-v1",
        "source_product_sha": "030bd50aff682592f67eba1dc5376b83bfe83fae",
        "prereg": "docs/v031-research/NATIVE_PACK_HELDOUT_O8C_PREREG.md",
        "family_results": {},
        "reps": REPS,
        "status": "EXECUTING",
    }
    before_env = os.environ.get(MICRO_PACK_ENV)
    with tempfile.TemporaryDirectory(prefix="cmpct-native-o8c-") as temp:
        home = Path(temp)
        for family in FAMILIES:
            contents = transformed(o8.population(family), "txt")
            source = home / family / "source"
            source.mkdir(parents=True)
            manifest = {}
            for name, data in sorted(contents.items()):
                (source / name).write_bytes(data)
                manifest[name] = hashlib.sha256(data).hexdigest()
            logical_bytes = sum(map(len, contents.values()))
            def source_manifest() -> dict:
                return {p.name: o8.hash_file(p) for p in source.iterdir()}
            assert source_manifest() == manifest
            builds: list[dict] = []
            reconstructions: list[dict] = []
            reference_hash: dict[str, str] = {}
            for rid in range(REPS):
                order = ("normal", "no_pack", "no_pack", "normal") if rid % 2 == 0 else (
                    "no_pack", "normal", "normal", "no_pack"
                )
                for trial, policy in enumerate(order):
                    archive = source.parent / f"trial-{rid}-{trial}-{policy}.cmpct"
                    record = build_controlled(source, archive, policy)
                    record.update(round=rid, trial=trial)
                    prior = reference_hash.setdefault(policy, record["archive_sha256"])
                    assert prior == record["archive_sha256"], (
                        family, policy, "nondeterministic archive bytes", prior, record["archive_sha256"]
                    )
                    builds.append(record)
                    assert source_manifest() == manifest, (family, "changed source")
                    # Both modes reconstruct all source bytes, sharing the exact built archive.
                    modes = ("serial", "group") if (rid + trial) % 2 == 0 else ("group", "serial")
                    for mode in modes:
                        dest = source.parent / f"out-{rid}-{trial}-{mode}"
                        raw = o8.run_trial(
                            binary, archive, dest, mode, f"{family}-{policy}",
                            rid, trial, manifest, logical_bytes
                        )
                        raw.update(archive_policy=policy, archive_sha256=record["archive_sha256"])
                        reconstructions.append(raw)
                    assert o8.hash_file(archive) == record["archive_sha256"], (
                        family, policy, "source archive mutated"
                    )
            assert os.environ.get(MICRO_PACK_ENV) == before_env
            observations = {}
            for policy in ("normal", "no_pack"):
                rows = [row for row in builds if row["policy"] == policy]
                crows = [row for row in reconstructions if row["archive_policy"] == policy]
                def med(key: str) -> float:
                    return statistics.median(row[key] for row in rows)
                def cmed(mode: str, key: str) -> float:
                    return statistics.median(row[key] for row in crows if row["mode"] == mode)
                sched = {(row["batch_count"], row["batched_members"], row["fallback"])
                         for row in crows if row["mode"] == "group"}
                assert len(sched) == 1, (family, policy, "unstable C group scheduling", sched)
                first = rows[0]
                batches, members, fallback = next(iter(sched))
                assert members + fallback == len(manifest)
                if policy == "no_pack":
                    assert batches == members == 0, (family, "no-pack control illegally admitted pack")
                observations[policy] = {
                    "archive_bytes": first["archive_bytes"],
                    "archive_sha256": first["archive_sha256"],
                    "build_wall_median_ms": med("create_wall_ms"),
                    "build_cpu_median_ms": med("create_cpu_ms"),
                    "serial_extract_wall_median_ms": cmed("serial", "wall_ms"),
                    "group_extract_wall_median_ms": cmed("group", "wall_ms"),
                    "serial_extract_cpu_median_ms": cmed("serial", "child_cpu_ms"),
                    "group_extract_cpu_median_ms": cmed("group", "child_cpu_ms"),
                    "serial_extract_rss_median_kib": cmed("serial", "rss_kib"),
                    "group_extract_rss_median_kib": cmed("group", "rss_kib"),
                    "batch_count": batches, "batched_members": members, "fallback_members": fallback,
                    "raw_builds": rows, "raw_extractions": crows,
                }
            packed = observations["normal"]["archive_bytes"]
            separate = observations["no_pack"]["archive_bytes"]
            result = {
                "files": len(manifest),
                "logical_bytes": logical_bytes,
                "same_path_manifest_sha256": hashlib.sha256(
                    json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "normal": observations["normal"],
                "no_pack": observations["no_pack"],
                "normal_minus_no_pack_bytes": packed - separate,
                "normal_over_no_pack_size_ratio": packed / separate,
                "normal_policy_size_loss": packed > separate,
            }
            report["family_results"][family] = result
            print(json.dumps({
                "family": family,
                "files": len(manifest),
                "normal_bytes": packed,
                "no_pack_bytes": separate,
                "delta_normal_minus_no_pack": packed - separate,
                "normal_batches": observations["normal"]["batch_count"],
                "normal_batched_members": observations["normal"]["batched_members"],
                "normal_create_wall_median_ms": observations["normal"]["build_wall_median_ms"],
                "no_pack_create_wall_median_ms": observations["no_pack"]["build_wall_median_ms"],
                "normal_group_extract_ms": observations["normal"]["group_extract_wall_median_ms"],
                "no_pack_group_extract_ms": observations["no_pack"]["group_extract_wall_median_ms"],
                "status": "SAME_PATH_EXACT_RECONSTRUCTION",
            }, sort_keys=True), flush=True)
    assert os.environ.get(MICRO_PACK_ENV) == before_env, "environment leak"
    report["status"] = "O8C_COMPLETE_WITH_NEGATIVES_PRESERVED"
    report["summary"] = {
        "families": len(FAMILIES),
        "builds": len(FAMILIES) * REPS * 4,
        "complete_c_extractions": len(FAMILIES) * REPS * 4 * 2,
        "normal_policy_size_loss_families": [
            name for name, result in report["family_results"].items()
            if result["normal_policy_size_loss"]
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
