#!/usr/bin/env python3
"""Installed-product streaming-salvage versus exact inherited framing scanner.

Measured separately from startup/import; ABBA order uses fresh child processes.
The synthetic physical input deliberately is NOT a valid CMPCT index, so this court
tests forensic framing and resource economics, not authenticated archive recovery.
"""
from __future__ import annotations

import binascii
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


DECLARED_KEYS = ("offset", "codec", "usize", "csize", "crc32", "sha256")


def inherited_scan(archive: Path):
    # Exact inherited algorithm and semantics from the v0.31 development source
    # before the candidate, except for formatting. Keep as a stronger control.
    from cmpct.codec import BHDR, BMAGIC
    data = Path(archive).read_bytes()
    out = []
    p = 0
    while True:
        i = data.find(BMAGIC, p)
        if i < 0:
            break
        if i + BHDR.size <= len(data):
            try:
                m, c, fl, res, us, cs, ml, rcrc, rh = BHDR.unpack_from(data, i)
                end = i + BHDR.size + ml + cs
                if end <= len(data):
                    out.append({
                        "offset": i, "codec": c, "usize": us,
                        "csize": cs, "crc32": rcrc, "sha256": bytes(rh).hex()
                    })
            except Exception:
                pass
        p = i + 1
    return out


def _worker(mode: str, path: Path):
    from cmpct.transactions import recover_blob_records
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start_cpu = time.process_time_ns()
    start = time.perf_counter_ns()
    rows = inherited_scan(path) if mode == "inherited" else recover_blob_records(path)
    wall_ns = time.perf_counter_ns() - start
    cpu_ns = time.process_time_ns() - start_cpu
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    keys = [{k: row[k] for k in DECLARED_KEYS} for row in rows]
    encoded = json.dumps(keys, sort_keys=True, separators=(",", ":")).encode()
    if mode == "candidate":
        assert all(row["verification"] == "unverified" for row in rows)
        assert all(row["generation_membership"] == "unknown" for row in rows)
    print(json.dumps({
        "mode": mode,
        "record_count": len(rows),
        "framing_sha256": hashlib.sha256(encoded).hexdigest(),
        "wall_ns": wall_ns, "cpu_ns": cpu_ns,
        "rss_before_kib": before, "rss_after_kib": after,
        "rss_increment_kib": max(0, after - before),
    }, sort_keys=True))


def _make_sparse(path: Path, size=64 * 1024 * 1024):
    from cmpct.codec import BHDR, BMAGIC, CODEC_RAW
    payload = b"FCMO-physical-header-candidate"
    fake_sha = bytes([0x42]) * 32
    frame = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(payload), len(payload), 0,
        binascii.crc32(payload) & 0xffffffff, fake_sha
    ) + payload
    offsets = [127, 1024 * 1024 - 17, 16 * 1024 * 1024 + 25, size - len(frame) - 8]
    with path.open("wb") as f:
        f.truncate(size)
        for o in offsets:
            f.seek(o)
            f.write(frame)
    return offsets


def _observe(path: Path, mode: str):
    p = subprocess.run([sys.executable, __file__, "--worker", mode, str(path)],
                       text=True, capture_output=True, check=True)
    return json.loads(p.stdout)


def main():
    with tempfile.TemporaryDirectory(prefix="cmpct-salvage-product-court-") as td:
        path = Path(td) / "physical-sparse.cmpct"
        expected_offsets = _make_sparse(path)
        st = path.stat()
        order = ["inherited", "candidate", "candidate", "inherited"] * 2
        samples = [_observe(path, mode) for mode in order]
        sig = {x["framing_sha256"] for x in samples}
        assert len(sig) == 1, "Framing/declared metadata changed versus inherited scanner"
        assert {x["record_count"] for x in samples} == {len(expected_offsets)}
        rss = {mode: [x["rss_increment_kib"] for x in samples if x["mode"] == mode]
               for mode in ("inherited", "candidate")}
        # This is a regression guard on the intended RAM mechanism, not a timing-win claim.
        assert max(rss["candidate"]) < 16 * 1024, rss
        assert min(rss["inherited"]) > 48 * 1024, rss
        med = {mode: {
            "wall_ms": statistics.median(x["wall_ns"] / 1e6 for x in samples if x["mode"] == mode),
            "cpu_ms": statistics.median(x["cpu_ns"] / 1e6 for x in samples if x["mode"] == mode),
            "incremental_peak_rss_mib": statistics.median(
                x["rss_increment_kib"] / 1024 for x in samples if x["mode"] == mode
            ),
        } for mode in ("inherited", "candidate")}
        print(json.dumps({
            "decision": "FRAMING_PARITY_AND_BOUNDED_SCAN_RSS",
            "scope": "real installed-product candidate vs copied inherited physical framing; not authenticated content recovery",
            "input": {"logical_bytes": st.st_size,
                      "physically_allocated_bytes": getattr(st, "st_blocks", 0) * 512,
                      "record_offsets": expected_offsets},
            "framing_sha256": next(iter(sig)),
            "raw_repeated_measurements": samples,
            "medians": med,
            "limitations": [
                "Linux ru_maxrss child process comparison; synthetic sparse file",
                "reader/decoder integrity and commitment ancestry are not measured",
                "CPU/wall are diagnostic; no product performance victory claimed",
                "result array memory remains proportional to number of candidate headers",
                "concurrent same-size source modification remains an unverified snapshot",
            ],
        }, sort_keys=True, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        _worker(sys.argv[2], Path(sys.argv[3]))
    else:
        main()
