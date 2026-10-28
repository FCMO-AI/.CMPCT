#!/usr/bin/env python3
"""J24C11: independent aggregate-clock causal check of J24C10 no-op control paths.

Research ONLY. Original J24C10 Q=1 result/threshold remains unchanged and negative.
Use an installed CMPCT wheel. Source and signed-wire identities are recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from test_o215_fixed_chunk_admission import _make_archive


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture(kind: str):
    if kind == "early-one":
        n = 65536
        blobs = (b"ABCD",)
        refs = [0] * n
        position = 12
        count = 8192
    elif kind == "late-ragged":
        n = 262144
        blobs = (b"ABCD", b"F", b"XY")
        refs = [i % len(blobs) for i in range(n)]
        position = None
        count = 16
    else:
        raise ValueError(kind)
    logical = b"".join(blobs[i] for i in refs)
    if position is None:
        position = len(logical) - 32
    wire = _make_archive(refs, logical, blobs=blobs)
    return wire, logical, position, count, n


def run_one(root: Path, kind: str, records: list):
    import cmpct.reader as reader_module
    import cmpct._chunk_admission as admission

    wire, logical, start, q, n = fixture(kind)
    archive = root / (kind + ".cmpct")
    archive.write_bytes(wire)
    expected_slice = logical[start:start + 16]
    expected_sha = sha(expected_slice * q)
    expected_wire_sha = sha(wire)
    original = admission._uniform_stride
    assert callable(original), "real native witness is unavailable"
    original_dispatch = reader_module.native_uniform_stride
    calls = {"count": 0}

    def counted_dispatch(storage, blobs, size):
        calls["count"] += 1
        return original_dispatch(storage, blobs, size)

    # The same counting proxy is installed for BOTH arms; no modified Reader.
    reader_module.native_uniform_stride = counted_dispatch
    try:
        with reader_module.CMPCT(archive) as reader:
            for arm in ("strict", "witness"):
                admission._uniform_stride = None if arm == "strict" else original
                # Symmetric untimed warmup, no changes to the protected path.
                for _ in range(2):
                    assert reader.read_range("fixed.bin", start, 16) == expected_slice
            assert calls["count"] == 0, (kind, "warmup called proof")
            for cycle in range(8):
                order = (("strict", "witness", "witness", "strict")
                         if cycle % 2 == 0 else
                         ("witness", "strict", "strict", "witness"))
                for order_index, arm in enumerate(order):
                    admission._uniform_stride = None if arm == "strict" else original
                    before_calls = calls["count"]
                    output = bytearray()
                    t0 = time.perf_counter_ns()
                    c0 = time.process_time_ns()
                    for _ in range(q):
                        output.extend(reader.read_range("fixed.bin", start, 16))
                    c1 = time.process_time_ns()
                    t1 = time.perf_counter_ns()
                    observed = sha(bytes(output))
                    assert observed == expected_sha, (kind, arm, cycle, observed)
                    delta_calls = calls["count"] - before_calls
                    assert delta_calls == 0, (kind, arm, "proof unexpectedly dispatched")
                    records.append(dict(kind=kind, n=n, arm=arm, cycle=cycle,
                                        order_index=order_index, repetitions=q,
                                        wire_sha256=expected_wire_sha,
                                        expected_answer_sha256=expected_sha,
                                        answer_sha256=observed,
                                        proof_dispatch_calls=delta_calls,
                                        wall_ns=t1 - t0, cpu_ns=c1 - c0,
                                        offset=start, length=16))
            assert calls["count"] == 0, (kind, "proof unexpectedly dispatched")
    finally:
        admission._uniform_stride = original
        reader_module.native_uniform_stride = original_dispatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    import cmpct.reader as reader_module
    import cmpct._chunk_admission as admission
    path = Path(reader_module.__file__).resolve()
    assert "site-packages" in path.parts or "dist-packages" in path.parts, path
    assert callable(admission._scan_refs) and callable(admission._uniform_stride)
    records = []
    with tempfile.TemporaryDirectory(prefix="j24c11-path-") as tmp:
        for kind in ("early-one", "late-ragged"):
            run_one(Path(tmp), kind, records)
    assert len(records) == 64

    groups = {}
    for row in records:
        groups.setdefault(row["kind"], {}).setdefault(row["arm"], []).append(row)
    summary = {}
    for kind, arms in sorted(groups.items()):
        strict = arms["strict"]
        witness = arms["witness"]
        sw = statistics.median(x["wall_ns"] for x in strict)
        ww = statistics.median(x["wall_ns"] for x in witness)
        sc = statistics.median(x["cpu_ns"] for x in strict)
        wc = statistics.median(x["cpu_ns"] for x in witness)
        summary[kind] = dict(strict_wall_median_ns=sw, witness_wall_median_ns=ww,
                             wall_ratio=sw / ww,
                             strict_cpu_median_ns=sc, witness_cpu_median_ns=wc,
                             cpu_ratio=(sc / wc if wc > 0 else None),
                             cpu_resolved=(sc > 0 and wc > 0),
                             zero_proof_dispatch=all(x["proof_dispatch_calls"] == 0
                                                     for xs in arms.values() for x in xs))
    output = dict(schema="j24c11-path-equivalence-v1",
                  source_head=subprocess.check_output(
                      ["git", "rev-parse", "HEAD"], text=True).strip(),
                  host=platform.system(), python=sys.version,
                  installed_reader=str(path), reader_sha256=sha(path.read_bytes()),
                  q_policy={"early-one": 8192, "late-ragged": 16},
                  records=records, summary=summary,
                  inherited_j24c10_q1_scientific_decision="NOT_PROMOTABLE",
                  release_credit=False)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print("J24C11_PATH_EQUIVALENCE", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
