#!/usr/bin/env python3
"""J24G90: physical source-exact r24 terminal checkpoint vs signed replay-prefix court.

Scientific evidence only: no product modification, new wire grammar or release credit.
The preregistration is committed before this instrument.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import struct
import sys
import tempfile
import time

import msgpack
import zstandard as zstd

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete, _append_generation

PRE_REG = "6383278886d678336197edf87683ecd98f119e7a"
RELEASE_MAIN = "80c358f8824ec1b20d349c92ed94c898090969b0"
READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"
NUMBERS = (4096, 8192)
DEPTH = 63
FOOTER = struct.Struct("<8sBBBBQQQ32s")
ORDERS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_receipt():
    import subprocess
    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert subprocess.run(["git", "merge-base", "--is-ancestor", PRE_REG, head],
                          cwd=root).returncode == 0
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
        cwd=root, text=True).strip()
    assert actual == READER_BLOB, (actual, READER_BLOB)
    return {"head": head, "prereg": PRE_REG, "released_main": RELEASE_MAIN,
            "reader_blob": actual}


def footer_receipt(raw: bytes):
    assert len(raw) >= FOOTER.size
    pos = len(raw) - FOOTER.size
    magic, kind, codec, flags, reserved, cs, us, previous, expected = FOOTER.unpack_from(raw, pos)
    assert magic == b"CMPTF24\x00" and kind in (0, 1)
    assert flags == reserved == 0 and cs > 0 and us > 0
    assert 0 <= previous < pos and cs <= pos
    encoded = raw[pos - cs:pos]
    if codec == 1:
        decoded = zstd.ZstdDecompressor().decompress(encoded, max_output_size=us)
    else:
        assert codec == 0
        decoded = encoded
    assert len(decoded) == us and hashlib.sha256(decoded).digest() == expected
    payload = msgpack.unpackb(decoded, raw=False)
    return {"footer_offset": pos, "kind": kind, "previous_footer": previous,
            "payload_sha256": digest(decoded), "payload_size": us,
            "payload": payload}


def index_fingerprint(index):
    return digest(msgpack.packb(index, use_bin_type=True))


def make_court(root: Path, n: int):
    source = root / ("source-" + str(n))
    source.mkdir()
    expected = {}
    for i in range(n):
        name = f"f{i:05d}.dat"
        raw = hashlib.sha256(f"j24g90-{n}-{i}".encode()).digest()
        (source / name).write_bytes(raw)
        expected[name] = digest(raw)
    a = root / f"a-{n}-prefix.cmpct"
    b = root / f"b-{n}-checkpoint.cmpct"
    c = root / f"c-{n}-bad-footer.cmpct"
    t0 = time.perf_counter_ns()
    Builder(source, workers=1, reproducible=False).build(a)
    for i in range(DEPTH):
        append_delete(a, f"f{i:05d}.dat")
        del expected[f"f{i:05d}.dat"]
    with CMPCT(a) as reader:
        assert reader.delta_depth == DEPTH
        base_index = msgpack.unpackb(msgpack.packb(reader.index, use_bin_type=True), raw=False)
        prev_footer = reader.latest_footer_pos
        fingerprint = index_fingerprint(base_index)
        assert len(reader.by) == n - DEPTH
    ar = a.read_bytes()
    af = footer_receipt(ar)
    assert af["kind"] == 1
    assert af["footer_offset"] == prev_footer
    shutil.copyfile(a, b)
    _append_generation(b, {"blobs": [], "ops": []},
                       prev_footer, checkpoint_index=base_index)
    br = b.read_bytes()
    bf = footer_receipt(br)
    assert bf["kind"] == 0 and bf["previous_footer"] == prev_footer
    assert bf["payload"] == base_index, "full snapshot must be identical logical state"
    assert br.startswith(ar), "checkpoint must append, not rewrite prior generations"
    shutil.copyfile(b, c)
    with c.open("r+b") as stream:
        stream.seek(-1, os.SEEK_END)
        original = stream.read(1)
        assert original
        stream.seek(-1, os.SEEK_END)
        stream.write(bytes([original[0] ^ 0x5A]))
    cr = c.read_bytes()
    try:
        footer_receipt(cr)
    except (AssertionError, ValueError, zstd.ZstdError):
        tamper_rejected = True
    else:
        tamper_rejected = False
    assert tamper_rejected
    return {
        "paths": {"A": a, "B": b, "C": c},
        "expected": expected,
        "index_sha256": fingerprint,
        "generation_seconds": (time.perf_counter_ns() - t0) / 1e9,
        "physical": {
            "A": {"size": len(ar), "sha256": digest(ar)},
            "B": {"size": len(br), "sha256": digest(br)},
            "C": {"size": len(cr), "sha256": digest(cr)}
        },
        "checkpoint_extra_bytes": len(br) - len(ar),
        "checkpoint_overhead_ratio": (len(br) - len(ar)) / len(ar),
        "previous_footer": prev_footer,
        "tampered_footer_rejected_independently": tamper_rejected,
    }


def check_semantics(case):
    receipts = {}
    expected = case["expected"]
    for label, path in case["paths"].items():
        with CMPCT(path) as reader:
            assert reader.delta_depth == (0 if label == "B" else DEPTH)
            assert reader.latest_footer_pos == (
                len(path.read_bytes()) - FOOTER.size if label == "B"
                else case["previous_footer"])
            assert index_fingerprint(reader.index) == case["index_sha256"]
            assert set(reader.by) == set(expected)
            assert reader.verify() == len(expected)
            for name in sorted(expected):
                assert digest(reader.read(name)) == expected[name], (label, name)
            receipts[label] = {
                "delta_depth": reader.delta_depth,
                "latest_footer": reader.latest_footer_pos,
                "index_sha256": index_fingerprint(reader.index),
                "verified_files": len(expected),
            }
    return receipts


def timed_open(path):
    # Windows process_time_ns has a coarse quantum on hosted CPython: sub-quantum
    # genuine Reader opens otherwise yield a zero CPU median. Hold exact source and
    # operation semantics fixed; amortize 64 fresh opens per reported sample there.
    batch = 64 if sys.platform == "win32" else 1
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    depths = set()
    for _ in range(batch):
        with CMPCT(path) as reader:
            assert len(reader.by) > 0
            depths.add(reader.delta_depth)
    assert len(depths) == 1, "inconsistent archive state within timed batch"
    return {"wall_ns": (time.perf_counter_ns() - t0) / batch,
            "cpu_ns": (time.process_time_ns() - c0) / batch,
            "depth": depths.pop(), "batch_repetitions": batch}

def measure(case):
    paths = case["paths"]
    for label in "ABC":
        for _ in range(3):
            timed_open(paths[label])
    samples = []
    for block in range(2):
        for order in ORDERS:
            for label in order:
                samples.append({"block": block, "order": order, "variant": label,
                                **timed_open(paths[label])})
    assert len(samples) == 36
    med = {metric: {label: statistics.median(
        x[metric] for x in samples if x["variant"] == label)
        for label in "ABC"} for metric in ("wall_ns", "cpu_ns")}
    return {
        "samples": samples, "medians": med,
        "A_over_B_wall_speedup": med["wall_ns"]["A"] / med["wall_ns"]["B"],
        "A_over_B_cpu_speedup": med["cpu_ns"]["A"] / med["cpu_ns"]["B"],
        "C_over_A_wall_ratio": med["wall_ns"]["C"] / med["wall_ns"]["A"],
    }


def main():
    output = Path(os.environ.get("J24G90_EVIDENCE", "evidence/j24g90"))
    output.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "cmpct-j24g90-terminal-checkpoint-v1",
               "source": source_receipt(),
               "host": platform.platform(), "python": sys.version,
               "product_credit": 0, "status": "RUNNING", "cases": {}}
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g90-") as td:
            root = Path(td)
            for n in NUMBERS:
                case = make_court(root, n)
                truth = check_semantics(case)
                benchmark = measure(case)
                for label, path in case["paths"].items():
                    saved = output / f"{n}-{label}.cmpct"
                    shutil.copyfile(path, saved)
                    assert digest(saved.read_bytes()) == case["physical"][label]["sha256"]
                record = {k: v for k, v in case.items() if k not in ("paths", "expected")}
                record.update({"semantics": truth, "timing": benchmark})
                receipt["cases"][str(n)] = record
        receipt["H1_survives"] = all(
            c["timing"]["A_over_B_wall_speedup"] >= 2.0 and
            c["timing"]["A_over_B_cpu_speedup"] >= 1.0
            for c in receipt["cases"].values())
        receipt["H2_survives"] = all(
            c["semantics"]["A"]["index_sha256"] ==
            c["semantics"]["B"]["index_sha256"] ==
            c["semantics"]["C"]["index_sha256"]
            and c["semantics"]["A"]["delta_depth"] == DEPTH
            and c["semantics"]["B"]["delta_depth"] == 0
            and c["semantics"]["C"]["delta_depth"] == DEPTH
            for c in receipt["cases"].values())
        assert receipt["H2_survives"], "corrupted-checkpoint recovery mismatch"
        receipt["status"] = "PASS"
    except BaseException as e:
        receipt["status"] = "FAIL"
        receipt["error"] = {"type": type(e).__name__, "message": str(e)}
        raise
    finally:
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
        print("J24G90_REPORT", json.dumps({
            "status": receipt["status"], "H1": receipt.get("H1_survives"),
            "H2": receipt.get("H2_survives"),
            "summary": {n: {
                "sizes": c["physical"],
                "extra_bytes": c["checkpoint_extra_bytes"],
                "wall_speedup": c["timing"]["A_over_B_wall_speedup"],
                "cpu_speedup": c["timing"]["A_over_B_cpu_speedup"],
                "recovery_ratio": c["timing"]["C_over_A_wall_ratio"],
            } for n,c in receipt["cases"].items()},
        }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("No positional args")
    main()
