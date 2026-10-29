#!/usr/bin/env python3
"""J24G33: installed #723 compaction + unchanged #613 sparse verifier, physical r24 court.

No monkeypatch, AST transplant or substitute Reader. All source and reconstructed
archives are real Builder/Writer revision-24 files; a fresh child measures RSS.
The previous #734 scientific A/B is a separate control, NOT this product result.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

PAGE = 4096
HEAD = b"H" * PAGE
TAIL = b"T" * PAGE
UPDATED = b"J24G33 committed delta" * 8
SIZES = (2 << 20, 128 << 20)
READER_BLOB = "b2b7774c13a5c8235ff89786d171b7ea3ff20710"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def create_source(work: Path, size: int) -> Path:
    from cmpct.builder import Builder
    from cmpct.codec import K_FILE, S_SPARSE
    from cmpct.reader import CMPCT
    from cmpct.transactions import append_update

    root = work / "source-tree"
    root.mkdir()
    sparse = root / "sparse.bin"
    with sparse.open("wb") as f:
        f.write(HEAD)
        f.seek(size - PAGE)
        f.write(TAIL)
    assert sparse.stat().st_blocks * 512 < size // 4, "host did not create real sparse allocation"
    (root / "small.bin").write_bytes(b"pre-journal payload")
    source = work / "source.cmpct"
    Builder(root, reproducible=True, workers=1).build(source)
    new = work / "replacement.bin"
    new.write_bytes(UPDATED)
    append_update(source, "small.bin", new)
    with CMPCT(source) as reader:
        row = reader.by["sparse.bin"]
        assert row[1] == K_FILE and row[6][0] == S_SPARSE
        assert row[4] == size
        assert reader.read_range("sparse.bin", 0, PAGE) == HEAD
        assert reader.read_range("sparse.bin", size - PAGE, PAGE) == TAIL
        assert reader.read("small.bin") == UPDATED
        assert reader.delta_depth >= 1, "compaction must remove a real committed journal"
    return source


def snapshot(path: Path, size: int) -> dict:
    from cmpct.codec import K_DIR, S_SPARSE
    from cmpct.reader import CMPCT
    from cmpct.transactions import _compaction_source_metadata
    with CMPCT(path) as reader:
        assert reader.by["sparse.bin"][6][0] == S_SPARSE
        assert reader.by["sparse.bin"][4] == size
        assert reader.read_range("sparse.bin", 0, PAGE) == HEAD
        assert reader.read_range("sparse.bin", size - PAGE, PAGE) == TAIL
        assert reader.read("small.bin") == UPDATED
        count = reader.verify()
        assert count == sum(row[1] != K_DIR for row in reader.files)
        return dict(
            rows=[tuple(row[:5]) for row in reader.files],
            hashes={row[0]: reader.file_sha256(row[0]).hex()
                    for row in reader.files if row[1] != K_DIR},
            metadata=_compaction_source_metadata(reader),
            verified=count,
            depth=reader.delta_depth,
        )


def child(source: Path, dest: Path, receipt: Path, size: int) -> None:
    from cmpct.transactions import compact_archive
    source_sha = digest(source)
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    outcome = compact_archive(source, dest)
    elapsed_wall = time.perf_counter_ns() - start_wall
    elapsed_cpu = time.process_time_ns() - start_cpu
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    before, after = snapshot(source, size), snapshot(dest, size)
    assert before["rows"] == after["rows"], "indexed file table drift"
    assert before["hashes"] == after["hashes"], "logical identity drift"
    assert before["metadata"] == after["metadata"], "metadata custody drift"
    assert before["depth"] >= 1 and after["depth"] == 0, "no actual journal compaction"
    assert digest(source) == source_sha, "source mutated during compaction"
    assert peak_kib < 128 * 1024 if size == 128 << 20 else True, (
        "logical hole verified by full-memory materialization", peak_kib
    )
    result = {
        "schema": "cmpct-j24g33-installed-r24-sparse-compaction-v1",
        "source_sha256": source_sha,
        "source_bytes": source.stat().st_size,
        "output_sha256": digest(dest),
        "output_bytes": dest.stat().st_size,
        "logical_sparse_bytes": size,
        "source_generation_depth": before["depth"],
        "output_generation_depth": after["depth"],
        "logical_sha256": after["hashes"],
        "source_metadata_equal": True,
        "index_rows_equal": True,
        "verified": after["verified"],
        "peak_rss_kib": peak_kib,
        "compaction_wall_ns": elapsed_wall,
        "compaction_cpu_ns": elapsed_cpu,
        "product_release_credit": 0,
    }
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


def negative(source: Path, destination: Path) -> dict:
    from cmpct.codec import BHDR, S_SPARSE
    from cmpct.reader import CMPCT
    from cmpct.transactions import compact_archive
    corrupted = source.with_name("corrupted.cmpct")
    shutil.copyfile(source, corrupted)
    with CMPCT(corrupted) as reader:
        row = reader.by["sparse.bin"]
        assert row[6][0] == S_SPARSE
        idx = row[6][1][0][2][0]
        offset, _, length, _, meta = reader.blobs[idx]
        pos = reader.record_base + offset + BHDR.size + meta
        assert length > 0
    physical = bytearray(corrupted.read_bytes())
    physical[pos] ^= 1
    corrupted.write_bytes(physical)
    sentinel = b"existing destination must remain byte-exact after bad source"
    destination.write_bytes(sentinel)
    try:
        compact_archive(corrupted, destination)
    except (OSError, ValueError, RuntimeError) as exc:
        assert destination.read_bytes() == sentinel, "unsafe failed publication"
        assert digest(source) != digest(corrupted)
        return {"rejected": True, "exception": type(exc).__name__,
                "destination_sha256": digest(destination),
                "corrupted_sha256": digest(corrupted)}
    raise AssertionError("corrupted physical sparse source published successfully")


def parent() -> None:
    artifacts = Path(os.environ["J24G33_ARTIFACT_DIR"])
    artifacts.mkdir(parents=True, exist_ok=True)
    findings = []
    for size in SIZES:
        with tempfile.TemporaryDirectory(prefix="j24g33-") as temp:
            work = Path(temp)
            source = create_source(work, size)
            initial_sha = digest(source)
            records = []
            for i in range(2):
                destination = work / f"compacted-{i}.cmpct"
                receipt = work / f"child-{i}.json"
                run = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--child",
                     str(size), str(source), str(destination), str(receipt)],
                    cwd=work, capture_output=True, text=True, timeout=300,
                    env={**os.environ, "CMPCT_ENCODE_WORKERS": "1"})
                (artifacts / f"{size}-{i}.stdout.txt").write_text(run.stdout)
                (artifacts / f"{size}-{i}.stderr.txt").write_text(run.stderr)
                if run.returncode:
                    raise AssertionError(
                        f"installed child exit {run.returncode}: {run.stderr[-3000:]}")
                record = json.loads(receipt.read_text())
                assert record["source_sha256"] == initial_sha
                assert record["logical_sparse_bytes"] == size
                records.append(record)
                shutil.copyfile(receipt, artifacts / f"receipt-{size}-{i}.json")
                shutil.copyfile(destination, artifacts / f"output-{size}-{i}.cmpct")
            assert len({r["output_sha256"] for r in records}) == 1, (
                "source-identical deterministic compaction changed output", records)
            assert digest(source) == initial_sha
            if size == SIZES[0]:
                hostile = negative(source, work / "protected.cmpct")
            else:
                hostile = None
            shutil.copyfile(source, artifacts / f"source-{size}.cmpct")
            findings.append({
                "logical_sparse_bytes": size, "source_sha256": initial_sha,
                "exact_repeat_output": True, "repeat_results": records,
                "physical_corruption_negative": hostile,
            })
    report = {
        "schema": "cmpct-j24g33-integrated-sparse-compaction-court-v1",
        "reader_source_blob": READER_BLOB,
        "cases": findings,
        "all_source_and_output_identity_checks": True,
        "disposition": "NARROW_INTEGRATED_CANDIDATE_EVIDENCE_NOT_RELEASE",
        "release_credit": 0,
    }
    (artifacts / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child(Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), int(sys.argv[2]))
    else:
        parent()
