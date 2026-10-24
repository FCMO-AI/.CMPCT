#!/usr/bin/env python3
"""O21: empirical installed-product cost of verify()+extractall() vs extractall().

Science only. Modes have different integrity semantics, so this is NOT a
same-semantics speed claim or a security proof against mutable sources.
Preregistered at docs/v031-research/2026-10-24-strong-extraction-economics-o21-prereg.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.codec import CODEC_RAW, K_FILE, S_BLOB, S_PACK
from cmpct.reader import CMPCT
from v031_pack_physical_sha_court import archive_bytes

MEMBERS = 256
FILE_SIZE = 768
RAW_SIZE = 4 * 1024 * 1024
BLOCKS = 5


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_manifest(source: Path) -> dict[str, str]:
    names = sorted(p for p in source.rglob("*") if p.is_file())
    return {p.relative_to(source).as_posix(): sha(p.read_bytes()) for p in names}


def create_corpora(base: Path) -> dict:
    result = {}
    pack_source = base / "pack-source"
    pack_source.mkdir()
    motif = (b"kind=config;owner=bounded;codec=pack;mode=immutable;"
             b"output=exact;reads=selective;verify=sha256;\n")
    for i in range(MEMBERS):
        prefix = f"entry={i:05d};component=worker;priority={i % 17:02d};\n".encode()
        raw = (prefix + motif * 12)[:FILE_SIZE].ljust(FILE_SIZE, b"-")
        (pack_source / f"entry-{i:05d}.txt").write_bytes(raw)
    pack_archive = base / "structured.cmpct"
    Builder(pack_source, workers=1, reproducible=True).build(pack_archive)
    result["structured_pack"] = register(
        pack_source, pack_archive, expected_storage=S_PACK, count=MEMBERS
    )

    raw_source = base / "direct-source"
    raw_source.mkdir()
    raw = hashlib.shake_256(b"CMPCT-O21-independent-direct-RAW").digest(RAW_SIZE)
    (raw_source / "direct.md").write_bytes(raw)
    raw_archive = base / "direct.cmpct"
    # Independent true revision-24 image. Reuse the immutable O1/#257 physical
    # fixture generator (whose physical SHA and CRC have independent controls).
    raw_archive.write_bytes(archive_bytes(raw, raw, packed=False))
    result["independent_direct_raw"] = register(
        raw_source, raw_archive, expected_storage=S_BLOB, count=1
    )
    return result


def register(source: Path, archive: Path, *, expected_storage: int, count: int) -> dict:
    original = source_manifest(source)
    assert len(original) == count
    physical = archive.read_bytes()
    with CMPCT(archive) as ar:
        regular = [r for r in ar.files if r[1] == K_FILE]
        assert len(regular) == count, (len(regular), count)
        assert all(r[6] and r[6][0] == expected_storage for r in regular), regular[:3]
        owners = sorted(set(int(r[6][1]) for r in regular))
        assert len(owners) == 1, owners
        if expected_storage == S_BLOB:
            assert ar.blobs[owners[0]][3] == CODEC_RAW, ar.blobs[owners[0]]
        if expected_storage == S_PACK:
            assert len(regular) >= 128 and ar.blobs[owners[0]][1] >= 100 * 1024
        assert ar.verify() == len(regular)
    return {
        "source": str(source),
        "archive": str(archive),
        "archive_sha256": sha(physical),
        "archive_bytes": len(physical),
        "original_manifest": original,
        "logical_bytes": sum((source / name).stat().st_size for name in original),
        "regular_entries": len(regular),
        "physical_owners": len(owners),
        "owner_codec": ar.blobs[owners[0]][3],
        "storage_kind": int(expected_storage),
    }


def child(archive: Path, expected_file: Path, destination: Path, mode: str) -> None:
    expected = json.loads(expected_file.read_text(encoding="utf-8"))
    assert sha(archive.read_bytes()) == expected["archive_sha256"]
    before_cpu = time.process_time_ns()
    before_wall = time.perf_counter_ns()
    with CMPCT(archive) as reader:
        after_open = time.perf_counter_ns()
        before_verify = after_open
        if mode == "verify_extract":
            assert reader.verify() == expected["regular_entries"]
        after_verify = time.perf_counter_ns()
        reader.extractall(destination, metadata=False)
        after_extract = time.perf_counter_ns()
    # O21b: the Reader operation ends before the independent filesystem SHA
    # oracle. Sample CPU at this exact same boundary as operation wall.
    cpu_after_extract = time.process_time_ns()
    observed = source_manifest(destination)
    assert observed == expected["original_manifest"], {
        "missing": sorted(set(expected["original_manifest"]) - set(observed)),
        "extra": sorted(set(observed) - set(expected["original_manifest"])),
        "bad_hashes": sorted(k for k in observed.keys() & expected["original_manifest"].keys()
                             if observed[k] != expected["original_manifest"][k]),
    }
    after_check = time.perf_counter_ns()
    audit_inclusive_cpu_ns = time.process_time_ns() - before_cpu
    operation_cpu_ns = cpu_after_extract - before_cpu
    print(json.dumps({
        "mode": mode,
        "open_ns": after_open - before_wall,
        "verify_ns": after_verify - before_verify,
        "extract_ns": after_extract - after_verify,
        "check_ns": after_check - after_extract,
        "total_operation_wall_ns": after_extract - before_wall,
        "total_operation_cpu_ns": operation_cpu_ns,
        "audit_inclusive_cpu_ns": audit_inclusive_cpu_ns,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_matches_sha256_manifest": True,
        "extracted_members": len(observed),
    }, sort_keys=True))


def run(out: Path | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-strong-extract-o21-") as td:
        root = Path(td)
        corpora = create_corpora(root)
        evidence = {}
        for corpus, meta in corpora.items():
            manifest = root / (corpus + "-manifest.json")
            manifest.write_text(json.dumps(meta, sort_keys=True))
            archive = Path(meta["archive"])
            samples = {"extract": [], "verify_extract": []}
            by_block = []
            for block in range(BLOCKS):
                order = (["extract", "verify_extract", "verify_extract", "extract"]
                         if block % 2 == 0
                         else ["verify_extract", "extract", "extract", "verify_extract"])
                block_samples = {"extract": [], "verify_extract": []}
                for arm in order:
                    destination = root / f"output-{corpus}-{block}-{arm}-{len(samples[arm])}"
                    cmd = [sys.executable, str(Path(__file__).resolve()), "--child",
                           "--archive", str(archive),
                           "--manifest", str(manifest), "--destination", str(destination),
                           "--mode", arm]
                    t0 = time.perf_counter_ns()
                    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
                    elapsed = time.perf_counter_ns() - t0
                    obs = json.loads(proc.stdout.strip())
                    assert obs["source_matches_sha256_manifest"]
                    obs["full_child_wall_ns"] = elapsed
                    samples[arm].append(obs)
                    block_samples[arm].append(obs)
                by_block.append({
                    "block": block,
                    "sequence": order,
                    "mean_extract_operation_ns": statistics.mean(
                        x["total_operation_wall_ns"] for x in block_samples["extract"]),
                    "mean_verified_operation_ns": statistics.mean(
                        x["total_operation_wall_ns"] for x in block_samples["verify_extract"]),
                })
            a = samples["extract"]
            b = samples["verify_extract"]
            def median(series, key):
                return statistics.median(x[key] for x in series)
            wall_a = median(a, "total_operation_wall_ns")
            wall_b = median(b, "total_operation_wall_ns")
            cpu_a = median(a, "total_operation_cpu_ns")
            cpu_b = median(b, "total_operation_cpu_ns")
            evidence[corpus] = {
                "archive": {k: v for k, v in meta.items()
                            if k not in ("source", "archive", "original_manifest")},
                "raw_samples": samples,
                "balanced_blocks": by_block,
                "median_operation_wall_ms": {
                    "extract": wall_a / 1e6, "verify_extract": wall_b / 1e6},
                "median_operation_cpu_ms": {
                    "extract": cpu_a / 1e6, "verify_extract": cpu_b / 1e6},
                "median_full_child_wall_ms": {
                    arm: median(series, "full_child_wall_ns") / 1e6
                    for arm, series in samples.items()},
                "median_peak_rss_kib": {
                    arm: median(series, "peak_rss_kib")
                    for arm, series in samples.items()},
                "ratio_verified_to_ordinary_wall": wall_b / wall_a,
                "ratio_verified_to_ordinary_cpu": cpu_b / cpu_a,
                "paired_block_wall_extra_ms": [
                    (v["mean_verified_operation_ns"] - v["mean_extract_operation_ns"]) / 1e6
                    for v in by_block],
            }
        result = {
            "status": "PASS",
            "classification": "SCOPED_INSTALLED_PRODUCT_RUNTIME_DIAGNOSTIC",
            "decision": "PRICE_STRONG_EXTRACTION_POLICY_NOT_SECURITY_OR_RELEASE_CREDIT",
            "controls": {
                "reader_blob_expected": "60f52328467ca509bb410abe6a34810c50917cb5",
                "physical_fixture_blob_expected": "2383bf9a8f7ce8a9a01028ccf1072169897df3f1",
                "host": sys.platform, "python": sys.version,
                "blocks": BLOCKS, "samples_per_arm_per_corpus": BLOCKS * 2,
                "different_integrity_semantics": True,
                "source_mutation_excluded_not_proven": True,
            },
            "corpora": evidence,
            "limitations": [
                "A and B differ in integrity guarantee; ratio is the cost of policy, not same-semantics speed",
                "Reader caches decoded physical owners within the same open handle",
                "Synthetic corpora; Linux one-runner cache/noise, no full product release ABBA",
                "No source snapshot or destination race protection; internal SHA not external signature",
                "Child peak RSS includes interpreter and package; no memory-traffic or I/O syscall trace",
            ],
        }
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(encoded, encoding="utf-8")
        print(encoded)
        return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path)
    p.add_argument("--child", action="store_true")
    p.add_argument("--archive", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--destination", type=Path)
    p.add_argument("--mode", choices=("extract", "verify_extract"))
    args = p.parse_args()
    if args.child:
        assert args.archive and args.manifest and args.destination and args.mode
        child(args.archive, args.manifest, args.destination, args.mode)
    else:
        run(args.out)


if __name__ == "__main__":
    main()
