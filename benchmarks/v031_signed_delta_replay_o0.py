#!/usr/bin/env python3
"""O0: authentic signed-r24 journal delta replay vs identical final checkpoint.

Scientific research only. This script neither changes CMPCT nor grants a release
performance claim. Builds one real physical owner using the installed Builder,
re-signs equivalent logical checkpoints, and uses CMPCT's own committed delta
writer. All measured reads/preflights use the exact installed implementation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

import msgpack

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_FILE, MAGIC, sha, zc, zd
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
import cmpct.validation as validation


PAYLOAD = b"DELTA-REPLAY-EXACT-CONTENT\x00"
SIZES = (128, 512, 2048, 4096)
REPEATS = 7


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checkpoint_with_reused_physical(source: Path, target: Path, count: int, prefix: str) -> dict:
    raw = source.read_bytes()
    magic, version, flags, csize, usize, dsize, commitment = HDR.unpack_from(raw)
    assert magic == MAGIC and version == 24 and flags == 0
    original_index = zd(raw[HDR.size:HDR.size + csize], usize)
    assert sha(original_index) == commitment
    index = msgpack.unpackb(original_index, raw=False)
    template = next(row for row in index["files"] if row[1] == K_FILE)
    assert len(index["files"]) == 1
    index["files"] = []
    for i in range(count):
        row = copy.deepcopy(template)
        row[0] = f"{prefix}{i:06d}.bin"
        index["files"].append(row)
    plain = msgpack.packb(index, use_bin_type=True)
    encoded = zc(plain, 12)
    physical = raw[HDR.size+csize:HDR.size+csize+dsize]
    wire = (
        HDR.pack(MAGIC, version, 0, len(encoded), len(plain), len(physical), sha(plain))
        + encoded + physical + encoded
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(plain), 0, sha(plain))
    )
    target.write_bytes(wire)
    assert sha(zd(encoded, len(plain))) == sha(plain)
    assert target.read_bytes()[HDR.size+len(encoded):HDR.size+len(encoded)+dsize] == physical
    return {"physical_sha256": digest(physical), "index_sha256": digest(plain),
            "index_bytes": len(plain), "full_bytes": len(wire)}


def make_case(root: Path, source: Path, n: int):
    initial = root / f"n{n}-before.cmpct"
    delta = root / f"n{n}-delta.cmpct"
    control = root / f"n{n}-checkpoint.cmpct"

    initial_info = checkpoint_with_reused_physical(source, initial, n, "f")
    control_info = checkpoint_with_reused_physical(source, control, n, "g")
    assert initial_info["physical_sha256"] == control_info["physical_sha256"]
    delta.write_bytes(initial.read_bytes())
    with CMPCT(delta) as reader:
        assert len(reader.index["files"]) == n
        prev = reader.latest_footer_pos
    ops = [["ren", f"f{i:06d}.bin", f"g{i:06d}.bin"] for i in range(n)]
    footer_pos, generation_bytes = _append_generation(delta, {"blobs": [], "ops": ops}, prev)
    assert footer_pos > prev
    assert generation_bytes > FTR.size

    # Product truth, not a simulated model: both archives present exactly the
    # same logical and physical members despite different signed journal history.
    dp = validation.preflight_archive(delta)
    cp = validation.preflight_archive(control)
    assert dp["files"] == cp["files"] == n
    assert dp["delta_depth"] == 1 and cp["delta_depth"] == 0
    with CMPCT(delta) as dr, CMPCT(control) as cr:
        assert dr.index == cr.index, "same logical-final-index control was violated"
        assert set(dr.by) == set(cr.by)
        for name in (f"g{0:06d}.bin", f"g{n//2:06d}.bin", f"g{n-1:06d}.bin"):
            assert dr.read(name) == cr.read(name) == PAYLOAD
    return delta, control, {
        "source_archive_sha256": digest(source.read_bytes()),
        "delta_sha256": digest(delta.read_bytes()),
        "checkpoint_sha256": digest(control.read_bytes()),
        "physical_sha256": initial_info["physical_sha256"],
        "delta_archive_bytes": delta.stat().st_size,
        "checkpoint_archive_bytes": control.stat().st_size,
        "checkpoint_index_bytes": control_info["index_bytes"],
        "generation_bytes": generation_bytes,
        "file_count": n, "operation_count": n,
        "generation_footer_offset": footer_pos,
        "result_index_equal": True,
    }


def measure_pair(delta: Path, control: Path, repeats: int):
    elapsed = {"delta": [], "checkpoint": []}
    cpu = {"delta": [], "checkpoint": []}
    replay_ns = {"delta": [], "checkpoint": []}
    orig = validation._apply_delta
    ticks = []

    def attributed(*a, **kw):
        start = time.perf_counter_ns()
        try:
            return orig(*a, **kw)
        finally:
            ticks.append(time.perf_counter_ns() - start)

    validation._apply_delta = attributed
    try:
        for repeat in range(repeats):
            # A/B B/A alternation to reduce temporal/cache-order bias.
            order = ("delta", "checkpoint") if repeat % 2 == 0 else ("checkpoint", "delta")
            for label in order:
                path = delta if label == "delta" else control
                ticks.clear()
                t0 = time.perf_counter_ns()
                c0 = time.process_time_ns()
                ans = validation.preflight_archive(path)
                c1 = time.process_time_ns()
                t1 = time.perf_counter_ns()
                assert ans["files"] > 0
                elapsed[label].append(t1-t0)
                cpu[label].append(c1-c0)
                replay_ns[label].append(sum(ticks))
                assert len(ticks) == (1 if label == "delta" else 0)
    finally:
        validation._apply_delta = orig

    def summary(values):
        return {"median_ms": statistics.median(values) / 1e6,
                "raw_ms": [round(t / 1e6, 6) for t in values]}
    return {
        "wall": {k: summary(v) for k, v in elapsed.items()},
        "cpu": {k: summary(v) for k, v in cpu.items()},
        "delta_replay_attribution": {k: summary(v) for k, v in replay_ns.items()},
        "wall_ratio_delta_over_checkpoint": (
            statistics.median(elapsed["delta"]) / statistics.median(elapsed["checkpoint"])
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=REPEATS)
    ap.add_argument("--sizes", type=int, nargs="+", default=list(SIZES))
    ns = ap.parse_args()
    if ns.repeats < 3 or any(n < 1 or n > 8192 for n in ns.sizes):
        raise SystemExit("invalid O0 workload")
    ns.out.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": "authenticated-r24-delta-replay-o0",
        "status": "RESEARCH_ONLY_NOT_RELEASE",
        "source_git_sha": os.environ.get("EVIDENCE_HEAD", "local-unpinned"),
        "host": platform.platform(),
        "python": sys.version,
        "sizes": {},
        "semantics": "same final index/content, differing signed-generation history",
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-delta-o0-") as td:
        tmp = Path(td)
        root = tmp / "input"
        root.mkdir()
        (root / "single.bin").write_bytes(PAYLOAD)
        source = tmp / "builder.cmpct"
        Builder(root, workers=1, reproducible=True).build(source)
        with CMPCT(source) as read:
            assert read.read("single.bin") == PAYLOAD
        for n in ns.sizes:
            delta, control, meta = make_case(tmp, source, n)
            measures = measure_pair(delta, control, ns.repeats)
            receipt["sizes"][str(n)] = {"identity": meta, "timing": measures}
            print("O0_CASE " + json.dumps({"n": n,
                  "wall_delta_ms": measures["wall"]["delta"]["median_ms"],
                  "wall_checkpoint_ms": measures["wall"]["checkpoint"]["median_ms"],
                  "replay_ms": measures["delta_replay_attribution"]["delta"]["median_ms"],
                  "complete_bytes_delta": meta["delta_archive_bytes"],
                  "complete_bytes_checkpoint": meta["checkpoint_archive_bytes"]}),
                  flush=True)
    out = ns.out / "delta-o0-receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"O0_RECEIPT={out} SHA256={digest(out.read_bytes())}", flush=True)


if __name__ == "__main__":
    main()
