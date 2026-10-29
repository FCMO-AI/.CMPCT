#!/usr/bin/env python3
"""J24M01d: replay the exact 256-MiB logical r24 archive retained from a failing full suite.

This is source/experiment evidence, not a product change or benchmark-promotion court.
The original test's child source is copied verbatim below.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ARCHIVE_SHA = "852a2e554cf2f984d9294858567168d6a39fe91ceb4ed16b83333158401a76f3"
SOURCE_LOGICAL_SHA = "50c7a6d6fe5cdff870a4c4041bf456719fef36f62bf693570cf128b6ff74a90e"
READER_BLOB = "f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "j24m01c_fullsuite_failure_r24.b64"

# EXACT original test child's code, from tests/test_j24v01_sparse_verify_streamed.py.
ORIGINAL = """
import json,resource,sys
from cmpct.reader import CMPCT
with CMPCT(sys.argv[1]) as reader:
    count=reader.verify()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({'verified':count,'peak_kib':peak}))
"""

# Separate, explicitly instrumented child. Its overhead is never attributed to the original.
STAGED = """
import hashlib,json,pathlib,resource,sys,time,os
def hwm(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
before=hwm()
t=time.perf_counter()
from cmpct.reader import CMPCT
import cmpct.reader as imported
imported_hwm=hwm()
path=pathlib.Path(imported.__file__).resolve()
data=path.read_bytes()
git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\\0'+data).hexdigest()
with CMPCT(sys.argv[1]) as reader:
    opened=hwm()
    row=reader.by['large.bin']
    count=reader.verify()
    end=hwm()
    result={'verified':count,'peak_kib':end,'before_import_kib':before,
      'after_import_kib':imported_hwm,'after_open_kib':opened,
      'reader_git_blob':git_blob,'reader_file':str(path),
      'logical_bytes':row[4],'logical_sha256':bytes(row[5]).hex(),
      'sparse_extent_bytes':sum(int(x[1]) for x in row[6][1]),
      'storage_tag':row[6][0],'retained_cache_count':len(reader.cache),
      'total_wall_ms':(time.perf_counter()-t)*1000}
print(json.dumps(result,sort_keys=True))
"""


def run_case(mode: str, archive: Path):
    code = ORIGINAL if mode == "original" else STAGED
    started = time.perf_counter_ns()
    p = subprocess.run([sys.executable, "-c", code, str(archive)],
                       capture_output=True, text=True, timeout=100)
    result = {"mode": mode, "exit": p.returncode, "wall_ms":
              (time.perf_counter_ns()-started)/1e6,
              "stdout": p.stdout[-1600:], "stderr": p.stderr[-1600:]}
    if p.returncode:
        raise RuntimeError(f"{mode} failed: {result}")
    d = json.loads(p.stdout.strip())
    if d.get("verified") != 1 or not isinstance(d.get("peak_kib"), int):
        raise AssertionError(f"invalid verification result: {result}")
    if mode == "staged":
        if d.get("reader_git_blob") != READER_BLOB:
            raise AssertionError(f"WRONG IMPORT: {d.get('reader_git_blob')} != {READER_BLOB}")
        if (d.get("logical_bytes") != 268435456 or
            d.get("logical_sha256") != SOURCE_LOGICAL_SHA or
            d.get("sparse_extent_bytes") != 8192 or
            d.get("storage_tag") != 3 or d.get("retained_cache_count") != 0):
            raise AssertionError(f"unexpected physical/logical semantics: {d}")
    result["observation"] = d
    return result


def main():
    raw = base64.b64decode(FIXTURE.read_text().strip(), validate=True)
    if len(raw) != 1160 or hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA:
        raise AssertionError("captured original physical archive mismatch")
    output = Path(os.environ.get("J24M01D_OUT", "j24m01d-results"))
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="j24m01d-exact-wire-") as folder:
        archive = Path(folder) / "large.cmpct"
        archive.write_bytes(raw)
        rows = [run_case(mode, archive) for mode in ("original","staged","staged","original")]
    origin_peaks = [r["observation"]["peak_kib"] for r in rows if r["mode"] == "original"]
    stage_peaks = [r["observation"]["peak_kib"] for r in rows if r["mode"] == "staged"]
    report = {
        "schema": "cmpct-j24m01d-same-archive-court-v1",
        "source_run": "40890827519", "source_artifact_id": 12903943709,
        "original_suite_peak_kib": 180344, "inherited_cap_kib": 131072,
        "physical_archive_sha256": ARCHIVE_SHA, "physical_archive_bytes": len(raw),
        "imported_reader_expected_git_blob": READER_BLOB,
        "original_peaks_kib": origin_peaks, "staged_peaks_kib": stage_peaks,
        "rows": rows, "release_credit": 0,
        "classification": ("reproduced_on_identical_wire" if max(origin_peaks) >= 131072 else
                           "NOT_REPRODUCED_ON_IDENTICAL_WIRE"),
        "claims_not_supported": ["general-suite failure repaired", "exact original failing child provenance",
                                 "cross-platform RSS bound", "product promotion"],
    }
    (output/"same-archive-results.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
