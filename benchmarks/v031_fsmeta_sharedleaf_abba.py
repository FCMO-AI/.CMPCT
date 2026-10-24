"""Scoped true-product ABBA: cost of pre-extraction fsmeta validation with opt-in atomic leaves.

This compares two *valid-archive* executions of the SAME CMPCT Reader:
  CANDIDATE: actual PR #303 validator;
  SHAM: temporarily no-op validator inside the exact same product method.
SHAM is not a shipping alternative, and this is NOT the r24/ZIP release comparator.
No comparator, workload, source archive or correctness assertion is weakened.
"""
from __future__ import annotations

from copy import deepcopy
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import tempfile
import time
import tracemalloc

import msgpack

from cmpct.codec import FTR, FMAGIC, HDR, sha, zc
from cmpct.core import Builder, CMPCT
from cmpct.validation import preflight_archive, _validate_fsmeta
import cmpct.reader as reader_module

LOGICAL = b"VALID-CMPCT-EXTRACTION-IDENTITY" * 512
OLD = b"EXTERNAL-HARDLINK-PRESERVE" * 13
CASES = (0, 1000, 10000)
REPETITIONS = 8


def _resigned_index(archive: Path, out: Path, nkeys: int) -> Path:
    original = archive.read_bytes()
    magic, ver, flags, comp, raw, bodylen, _ = HDR.unpack_from(original)
    body = original[HDR.size + comp:HDR.size + comp + bodylen]
    with CMPCT(archive) as reader:
        index = deepcopy(reader.index)
        assert [x[0] for x in reader.files] == ["payload.bin"]
    if nkeys:
        index["fsmeta"]["xattrs"] = [[0, [
            [f"user.fsmeta_cost_{i:05d}", bytes([i % 251])] for i in range(nkeys)
        ]]]
    packed = msgpack.packb(index, use_bin_type=True)
    packed_zstd = zc(packed, 12)
    digest = sha(packed)
    out.write_bytes(
        HDR.pack(magic, ver, flags, len(packed_zstd), len(packed), len(body), digest)
        + packed_zstd + body + packed_zstd
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed_zstd), len(packed), 0, digest)
    )
    return out


def _one_case(root: Path, archive: Path, nkeys: int) -> dict:
    # Validate the actual signed r24 grammar independently before sham attribution.
    assert preflight_archive(archive)["files"] == 1
    dest = root / f"destination-{nkeys}"
    dest.mkdir()
    leaf = dest / "payload.bin"
    outside = root / f"outside-{nkeys}"
    outside.write_bytes(OLD)
    original_validator = reader_module._validate_fsmeta
    assert original_validator is _validate_fsmeta, "wrong product owner imported"
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.read("payload.bin") == LOGICAL
        original_idx = (outside.stat().st_dev, outside.stat().st_ino)
        samples = {"validated": [], "sham": []}

        def extract(mode: str, measured: bool):
            # Reset physical alias outside timing, so both modes have identical starting inode graph.
            if leaf.exists(): leaf.unlink()
            os.link(outside, leaf)
            assert leaf.samefile(outside) and leaf.stat().st_nlink == 2
            gc.collect()
            if mode == "sham":
                reader_module._validate_fsmeta = lambda _meta, _count: None
            else:
                reader_module._validate_fsmeta = original_validator
            try:
                w0 = time.perf_counter_ns()
                c0 = time.process_time_ns()
                reader.extractall(dest, metadata=False, atomic_shared_leaf=True)
                cpu = time.process_time_ns() - c0
                wall = time.perf_counter_ns() - w0
            finally:
                reader_module._validate_fsmeta = original_validator
            assert leaf.read_bytes() == LOGICAL
            assert outside.read_bytes() == OLD
            assert (outside.stat().st_dev, outside.stat().st_ino) == original_idx
            assert leaf.stat().st_ino != outside.stat().st_ino
            assert not list(dest.glob(".cmpct-part-*"))
            if measured:
                samples[mode].append({"wall_ms": wall / 1e6, "cpu_ms": cpu / 1e6})

        for mode in ("validated", "sham", "sham", "validated"):
            extract(mode, measured=False)
        for rep in range(REPETITIONS):
            order = ("validated", "sham", "sham", "validated") if rep % 2 == 0 else (
                "sham", "validated", "validated", "sham")
            for mode in order:
                extract(mode, measured=True)

        # Measure the allocation of the grammar pass separately, not contaminating timed extraction.
        tracemalloc.start()
        try:
            tracemalloc.reset_peak()
            _validate_fsmeta(reader.fsmeta, len(reader.files))
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

    stats = {}
    for mode in samples:
        for metric in ("wall_ms", "cpu_ms"):
            stats[f"{mode}_{metric}_median"] = statistics.median(
                x[metric] for x in samples[mode])
    return {
        "xattr_pairs": nkeys, "archive_bytes": archive.stat().st_size,
        "valid_grammar": True, "exact_source_bytes": len(LOGICAL),
        "peak_python_allocation_bytes_validator_only": peak,
        "measurements": samples, "medians": stats,
        "interpretation": "same-engine validator-ablation attribution, NOT historical or release parity",
    }


def main() -> None:
    if os.name != "posix" or not hasattr(os, "link"):
        raise RuntimeError("requires POSIX hardlinks")
    with tempfile.TemporaryDirectory(prefix="cmpct-fsmeta-cost-") as t:
        root = Path(t)
        source = root / "source"
        source.mkdir()
        (source / "payload.bin").write_bytes(LOGICAL)
        archive = root / "baseline.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        results = []
        for nkeys in CASES:
            altered = _resigned_index(archive, root / f"valid-{nkeys}.cmpct", nkeys)
            results.append(_one_case(root, altered, nkeys))

    report = {
        "head_sha": os.getenv("GITHUB_SHA", "LOCAL-UNATTESTED"),
        "timestamp_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "platform": platform.platform(), "python": platform.python_version(),
        "n_repetitions": REPETITIONS,
        "comparators": "same Reader and archive; validated vs sham no-op ONLY on valid metadata",
        "release_claim": "NONE — no historical exact-engine comparison or portable RSS gate",
        "cases": results,
    }
    path = Path("benchmark-artifacts") / "v031_fsmeta_sharedleaf_abba.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    for item in results:
        m = item["medians"]
        print(
            "VALID_FS_META", item["xattr_pairs"], "pairs archive", item["archive_bytes"],
            "bytes; validated", round(m["validated_wall_ms_median"], 5), "ms sham",
            round(m["sham_wall_ms_median"], 5), "ms peak_validator",
            item["peak_python_allocation_bytes_validator_only"], "B"
        )
    print("ALL_SAME_SOURCE_LOGICAL_HASHES_AND_EXTERNAL_HARDLINK_INODES_PRESERVED")


if __name__ == "__main__":
    main()
