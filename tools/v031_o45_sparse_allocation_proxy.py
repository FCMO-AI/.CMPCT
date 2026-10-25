#!/usr/bin/env python3
"""O45: source-exact Linux preallocation/SEEK_DATA/Builder structural falsifier.

Research-only. Never changes the official release corpus, comparator or product source.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import time
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_SPARSE, S_CDC, S_BLOB
from tools.v031_release_corpus_semantic_witness import semantic_release_tree_sha256

SIZE = 8 * 1024 * 1024
TAIL = hashlib.shake_256(b"cmpct-o45-source-independent-terminal-extent").digest(4096)
NANO_MTIME = 1_600_000_000_000_000_000
KIND_NAMES = {S_SPARSE: "S_SPARSE", S_CDC: "S_CDC", S_BLOB: "S_BLOB"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def logical_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def extent_observation(path: Path) -> dict:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        out = {"st_blocks_512": int(st.st_blocks), "charged_bytes": int(st.st_blocks) * 512,
               "st_size": int(st.st_size), "inode": int(st.st_ino), "dev": int(st.st_dev),
               "mode": stat.S_IMODE(st.st_mode), "mtime_ns": int(st.st_mtime_ns)}
        for name in ("SEEK_DATA", "SEEK_HOLE"):
            try:
                out[name.lower()] = int(os.lseek(fd, 0, getattr(os, name)))
            except OSError as exc:
                if exc.errno != errno.ENXIO:
                    raise
                out[name.lower()] = None
        return out
    finally:
        os.close(fd)


def restore_mtime(path: Path) -> None:
    os.chmod(path, 0o644)
    os.utime(path, ns=(NANO_MTIME, NANO_MTIME))


def establish_sparse(path: Path) -> None:
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o644)
    try:
        os.ftruncate(fd, 0)
        os.ftruncate(fd, SIZE)
        assert os.pwrite(fd, TAIL, SIZE - len(TAIL)) == len(TAIL)
    finally:
        os.close(fd)
    restore_mtime(path)


def establish_preallocated(path: Path) -> None:
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        os.posix_fallocate(fd, 0, SIZE)
    finally:
        os.close(fd)
    restore_mtime(path)


def establish_written_dense(path: Path) -> None:
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        zero = bytes(1024 * 1024)
        for offset in range(0, SIZE, len(zero)):
            assert os.pwrite(fd, zero, offset) == len(zero)
        assert os.pwrite(fd, TAIL, SIZE - len(TAIL)) == len(TAIL)
    finally:
        os.close(fd)
    restore_mtime(path)


def evaluate(name: str, root: Path, outroot: Path, expected_head: str) -> dict:
    path = root / "payload.bin"
    physical = extent_observation(path)
    semantic = semantic_release_tree_sha256(root)
    h = logical_sha(path)
    archive = outroot / (name + ".cmpct")
    t0 = time.perf_counter_ns()
    build = Builder(root, workers=1, reproducible=True).build(archive)
    build_ns = time.perf_counter_ns() - t0
    with CMPCT(archive) as reader:
        rows = [row for row in reader.files if row[0] == "payload.bin"]
        assert len(rows) == 1
        storage = rows[0][6]
        kind = int(storage[0])
        reader.verify()
        retrieved = reader.read("payload.bin")
        assert hashlib.sha256(retrieved).hexdigest() == h
        assert len(retrieved) == SIZE
        destination = outroot / ("extract-" + name)
        reader.extractall(destination, metadata=False)
    assert logical_sha(destination / "payload.bin") == h
    assert physical["st_size"] == SIZE
    return {
        "name": name, "physical": physical, "logical_sha256": h,
        "o42_semantic_tree_sha256": semantic,
        "storage_kind": KIND_NAMES.get(kind, str(kind)),
        "full_archive_bytes": archive.stat().st_size,
        "full_archive_sha256": logical_sha(archive),
        "builder_metrics": build,
        "build_wall_ns_descriptive_not_benchmark": build_ns,
        "source_head": expected_head,
        "verify": "PASS", "read": "EXACT", "extractall": "EXACT",
    }


def run(output: Path, expected_head: str, scratch_dir: Path | None = None) -> dict:
    actual_head = git("rev-parse", "HEAD")
    if actual_head != expected_head:
        raise RuntimeError(f"source HEAD mismatch: {actual_head} != {expected_head}")
    if not hasattr(os, "posix_fallocate") or not hasattr(os, "SEEK_DATA"):
        raise RuntimeError("UNSUPPORTED_HOST: no Linux preallocation/SEEK_DATA")
    with tempfile.TemporaryDirectory(prefix="cmpct-o45-",
                                          dir=str(scratch_dir) if scratch_dir else None) as tmp:
        root = Path(tmp) / "source"
        outroot = Path(tmp) / "results"
        root.mkdir()
        outroot.mkdir()
        path = root / "payload.bin"
        establish_sparse(path)
        sparse = evaluate("sparse", root, outroot, actual_head)
        # A second unchanged-source build is an independent determinism control.
        sparse_repeat = evaluate("sparse_repeat", root, outroot, actual_head)
        establish_preallocated(path)
        preallocated = evaluate("preallocated", root, outroot, actual_head)
        establish_written_dense(path)
        written = evaluate("written_dense", root, outroot, actual_head)
        establish_sparse(path)
        sparse_restored = evaluate("sparse_restored", root, outroot, actual_head)

    rows = [sparse, sparse_repeat, preallocated, written, sparse_restored]
    initial = sparse
    comparable = all(row["o42_semantic_tree_sha256"] == initial["o42_semantic_tree_sha256"]
                     and row["logical_sha256"] == initial["logical_sha256"]
                     and row["physical"]["inode"] == initial["physical"]["inode"]
                     and row["physical"]["dev"] == initial["physical"]["dev"]
                     and row["physical"]["mode"] == initial["physical"]["mode"]
                     and row["physical"]["mtime_ns"] == initial["physical"]["mtime_ns"]
                     for row in rows)
    control_identical = (
        sparse["full_archive_sha256"] == sparse_repeat["full_archive_sha256"]
        == sparse_restored["full_archive_sha256"]
    )
    allocation_changed = (
        initial["physical"]["charged_bytes"] < 0.75 * SIZE
        and preallocated["physical"]["charged_bytes"] >= 0.75 * SIZE
        and written["physical"]["charged_bytes"] >= 0.75 * SIZE
    )
    # On ext4, fallocate creates unwritten extents; SEEK_DATA commonly skips them.
    physical_hole_agreement = (
        initial["physical"]["seek_data"] == preallocated["physical"]["seek_data"]
        and (initial["physical"]["seek_data"] or 0) > 0
        and written["physical"]["seek_data"] == 0
    )
    storage_changed = (
        sparse["storage_kind"] == "S_SPARSE"
        and preallocated["storage_kind"] != "S_SPARSE"
        and written["storage_kind"] != "S_SPARSE"
    )
    verdict = (
        "SUPPORTED_SAME_HOLE_TOPOLOGY_ALLOCATION_PROXY_FALSE_NEGATIVE"
        if comparable and control_identical and allocation_changed and physical_hole_agreement
           and storage_changed
        else "NOT_SUPPORTED_ON_THIS_HOST"
    )
    result = {
        "schema": "cmpct-o45-source-exact-sparse-allocation-proxy-v1",
        "source_head": actual_head,
        "scratch_parent": str(scratch_dir) if scratch_dir else tempfile.gettempdir(),
        "builder_git_blob": git("rev-parse", "HEAD:src/cmpct/builder.py"),
        "codec_git_blob": git("rev-parse", "HEAD:src/cmpct/codec.py"),
        "witness_git_blob": git("rev-parse", "HEAD:tools/v031_release_corpus_semantic_witness.py"),
        "case_logical_bytes": SIZE,
        "baseline_o42_semantic_digest_invariant": comparable,
        "unchanged_sparse_output_reproducible": control_identical,
        "allocation_prefilter_crossed": allocation_changed,
        "unwritten_hole_topology_preserved": physical_hole_agreement,
        "physical_representation_changed": storage_changed,
        "preallocation_minus_sparse_archive_bytes": (
            preallocated["full_archive_bytes"] - sparse["full_archive_bytes"]),
        "written_minus_sparse_archive_bytes": (
            written["full_archive_bytes"] - sparse["full_archive_bytes"]),
        "cases": rows,
        "verdict": verdict,
        "evidence_class": "research-only; no official benchmark, product, promotion or release credit",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not (comparable and control_identical and allocation_changed and storage_changed):
        raise RuntimeError("O45 evidence contradiction: "+verdict)
    # Do not force the host-specific SEEK_DATA equivalence: preserve genuine negative result.
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--scratch-dir", type=Path, default=None)
    args = parser.parse_args()
    run(args.output, args.expected_head, args.scratch_dir)


if __name__ == "__main__":
    main()
