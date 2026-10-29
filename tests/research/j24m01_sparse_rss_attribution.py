#!/usr/bin/env python3
"""J24M01: read-only source-exact attribution of the inherited 256-MiB sparse RSS failure.

The ordinary full-suite test and its threshold remain unchanged. This evidence instrument
is not an alternate performance gate or an optimization candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

EXPECTED_READER_BLOB = "f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f"
MIB = 1024 * 1024


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(MIB)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sample() -> dict:
    status = {}
    path = Path("/proc/self/status")
    if path.exists():
        for line in path.read_text().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                if key in ("VmRSS", "VmHWM", "RssAnon", "RssFile", "VmPeak"):
                    status[key] = int(value.strip().split()[0])
    usage = resource.getrusage(resource.RUSAGE_SELF)
    status.update(ru_maxrss_kib=usage.ru_maxrss, utime_s=usage.ru_utime,
                  stime_s=usage.ru_stime, inblock=usage.ru_inblock,
                  oublock=usage.ru_oublock)
    return status


def child(path: Path, expected_sha: str, instrument: bool) -> None:
    stages = {"before_cmpct_import": sample()}
    t0 = time.perf_counter_ns()
    import cmpct.reader as reader_module
    from cmpct.reader import CMPCT
    from cmpct.codec import S_SPARSE
    imported_file = Path(reader_module.__file__).resolve()
    imported_blob = subprocess.check_output(
        ["git", "hash-object", str(imported_file)], text=True).strip()
    assert imported_blob == EXPECTED_READER_BLOB, (imported_file, imported_blob)
    stages["after_cmpct_import"] = sample()
    counts = {"calls": 0, "decoded_bytes": 0, "largest_decoded_blob": 0}
    with CMPCT(path) as ar:
        row = ar.by["large.bin"]
        assert row[6][0] == S_SPARSE and bytes(row[5]).hex() == expected_sha
        extents = [{"offset": off, "logical_data_bytes": size, "blob_count": len(ids)}
                   for off, size, ids in row[6][1]]
        stages["after_reader_open"] = sample()
        if instrument:
            original = ar._blob
            def counted(index, *, retain=True):
                data = original(index, retain=retain)
                counts["calls"] += 1
                counts["decoded_bytes"] += len(data)
                counts["largest_decoded_blob"] = max(
                    counts["largest_decoded_blob"], len(data))
                return data
            ar._blob = counted
        verified = ar.verify()
        stages["after_verify"] = sample()
        retained_cache_bytes = sum(len(value) for value in ar.cache.values())
    stages["after_reader_close"] = sample()
    assert verified == 1, verified
    assert all(stages["after_verify"]["VmHWM"] >= stages[k]["VmHWM"]
               for k in ("before_cmpct_import", "after_cmpct_import",
                         "after_reader_open")), stages
    row_output = {
        "schema": "cmpct-j24m01-child-v1",
        "pid": os.getpid(),
        "python": sys.version.split()[0],
        "imported_reader_path": str(imported_file),
        "imported_reader_git_blob": imported_blob,
        "archive_sha256": digest_file(path),
        "logical_size": row[4],
        "indexed_logical_sha256": bytes(row[5]).hex(),
        "physical_data_extent_bytes": sum(x["logical_data_bytes"] for x in extents),
        "extents": extents,
        "verified": verified,
        "instrumented": instrument,
        "decoded_blob_accounting": counts if instrument else None,
        "retained_cache_bytes": retained_cache_bytes,
        "stages": stages,
        "total_wall_ms": round((time.perf_counter_ns() - t0) / 1e6, 4),
        "legacy_full_suite_cap_kib": 128 * 1024,
    }
    print(json.dumps(row_output, sort_keys=True))


def build_fixtures(root: Path) -> list[dict]:
    from cmpct.builder import Builder
    from cmpct.codec import S_SPARSE
    from cmpct.reader import CMPCT

    out = []
    for mib in (2, 128, 256):
        case = root / f"sparse-{mib}"
        tree = case / "tree"
        tree.mkdir(parents=True)
        huge = tree / "large.bin"
        with huge.open("wb") as f:
            f.write(b"J24V01" * 512)
            f.seek(mib * MIB - 4096)
            f.write(b"V" * 4096)
        st = huge.stat()
        archive = case / "large.cmpct"
        Builder(tree).build(archive)
        with CMPCT(archive) as ar:
            row = ar.by["large.bin"]
            assert row[6][0] == S_SPARSE and row[4] == mib * MIB
            extents = [[off, n, len(ids)] for off, n, ids in row[6][1]]
            expected = bytes(row[5]).hex()
        assert digest_file(huge) == expected
        out.append({
            "mib": mib,
            "logical_sha256": expected,
            "logical_file_blocks": st.st_blocks,
            "logical_file_allocated_bytes": st.st_blocks * 512,
            "archive_path": str(archive),
            "archive_sha256": digest_file(archive),
            "archive_bytes": archive.stat().st_size,
            "physical_data_extent_bytes": sum(e[1] for e in extents),
            "extents": extents,
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--instrument", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--sha")
    args = parser.parse_args()
    if args.child:
        assert args.archive and args.sha
        child(args.archive, args.sha, args.instrument)
        return
    assert args.receipt, "--receipt is required"
    root = args.receipt.parent
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24m01-") as temp:
        cases = build_fixtures(Path(temp))
        measurements = []
        for case in cases:
            for instrument in (False, True, False):
                cmd = [sys.executable, __file__, "--child",
                       "--archive", case["archive_path"],
                       "--sha", case["logical_sha256"]]
                if instrument:
                    cmd.append("--instrument")
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=120, check=True)
                data = json.loads(proc.stdout.strip().splitlines()[-1])
                assert data["archive_sha256"] == case["archive_sha256"]
                assert data["imported_reader_git_blob"] == EXPECTED_READER_BLOB
                assert data["verified"] == 1
                assert data["physical_data_extent_bytes"] == case["physical_data_extent_bytes"]
                measurements.append({"case_mib": case["mib"], **data})
        receipt = {
            "schema": "cmpct-j24m01-stage-attribution-v1",
            "science_only": True,
            "product_change": False,
            "release_credit": 0,
            "source_reader_git_blob": EXPECTED_READER_BLOB,
            "cases": cases,
            "measurements": measurements,
            "conclusion": "UNADJUDICATED_MEASUREMENTS_ONLY",
        }
        # The original source fixtures live only in the temporary working directory.
        # Preserve raw SHA/physical extents/measurements, never fabricate artifact files.
        args.receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        print(json.dumps({"receipt": str(args.receipt),
                          "peaks": [{"mib": m["case_mib"],
                                     "instrumented": m["instrumented"],
                                     "peak_kib": m["stages"]["after_verify"]["VmHWM"],
                                     "import_kib": m["stages"]["after_cmpct_import"]["VmHWM"],
                                     "open_kib": m["stages"]["after_reader_open"]["VmHWM"],
                                     "decoded": m["decoded_blob_accounting"]}
                                    for m in measurements]}, sort_keys=True))


if __name__ == "__main__":
    main()
