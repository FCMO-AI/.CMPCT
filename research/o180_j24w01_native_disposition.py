#!/usr/bin/env python3
"""O180 independent disposition: classify J24W01 against original O171 truth.
The native court, historical negative, and O167 positive are never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import traceback

SCHEMA = "cmpct-o180-j24w01-same-archive-decision-v1"
DONOR = "7436bb34e5019639b8e00541b437b5153dee7462"
READER_BLOB = "88b6706ba748306b6a4a13274fff2220eec0c32a"
HELPER_BLOB = "70308f454c74fad7b247db6ee36aa8cc7d38c99c"
O171_BLOB = "8c943128f135607dd36abd083bf1019bc9e4433a"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decide(a: argparse.Namespace, out: dict) -> None:
    receipt, baseline, positive, candidate, court = (
        load(a.receipt), load(a.baseline), load(a.positive), load(a.candidate), load(a.court)
    )
    archive = digest(a.archive)
    out["archive_sha256"] = archive
    out["archive_bytes"] = a.archive.stat().st_size
    if (receipt.get("schema") != "cmpct-o165-linux-origin-receipt-v1"
        or archive != receipt.get("archive_sha256")
        or out["archive_bytes"] != receipt.get("archive_bytes")):
        raise AssertionError("Linux artifact not source-identical")
    if baseline.get("result") != "HISTORICAL_O171_NOTIMPLEMENTED_ERROR_REPRODUCED":
        raise AssertionError("historical negative control did not reproduce")
    if positive.get("result") != "EXACT_O167_WIN32_CROSSHOST_TOPOLOGY_VERIFIED":
        raise AssertionError("original exact O167 positive control did not reproduce")
    if any(x.get("archive_sha256") != archive for x in (baseline, positive, candidate)):
        raise AssertionError("comparison used different archives")
    if candidate.get("source_sha") != DONOR or candidate.get("final_archive_sha256") != archive:
        raise AssertionError("J24W01 candidate source or archive custody lost")
    files = candidate.get("installed_files") or {}
    if files.get("src/cmpct/reader.py", {}).get("git_blob") != READER_BLOB:
        raise AssertionError("J24W01 installed Reader not source-authenticated")
    if files.get("src/cmpct/_win32_times.py", {}).get("git_blob") != HELPER_BLOB:
        raise AssertionError("J24W01 installed helper not source-authenticated")
    if candidate.get("unaltered_original_o171_court_blob") != O171_BLOB:
        raise AssertionError("original O171 physical court changed")
    if not all(info.get("installed_outside_source") and
               (info.get("byte_identical") or info.get("only_crlf_difference"))
               for info in files.values()):
        raise AssertionError("candidate not independently installed with exact source")
    if court.get("expected_archive_sha256") != archive or not court.get("original_archive_exact"):
        raise AssertionError("original O171 court did not authenticate archive")

    verify = court.get("installed_verify") or {}
    extract = court.get("installed_extract") or {}
    out["original_court_result"] = court.get("result")
    out["original_court_verify_rc"] = verify.get("returncode")
    out["original_court_extract_rc"] = extract.get("returncode")
    out["candidate_python_error"] = candidate.get("error")
    if verify.get("returncode") != 0:
        raise AssertionError("J24W01 verify failed; not a symlink restoration regression")
    if (court.get("result") == "ONE_AUTHENTIC_LINUX_ARCHIVE_WIN32_SCOPED_PHYSICAL_FIDELITY_VERIFIED"
        and extract.get("returncode") == 0
        and candidate.get("result") == "J24W01_SCOPED_WIN32_TOPOLOGY_VERIFIED"
        and candidate.get("archive_unchanged") is True):
        out["decision"] = "HYPOTHESIS_FALSIFIED_J24W01_PASSES_ORIGINAL_O171"
        out["evidence_class"] = "native installed-product falsification"
    else:
        errors = extract.get("stderr_tail") or ""
        cap = court.get("host_capabilities") or {}
        if (court.get("result") != "WIN32_EXTRACTION_REJECTED_AFTER_VALID_VERIFY"
            or extract.get("returncode") in (0, None)
            or not all(token in errors for token in
                       ("NotImplementedError", "follow_symlinks", "utime"))
            or not all(cap.get(key) is True for key in
                       ("hardlink_created", "symlink_created", "directory_symlink_created"))):
            raise AssertionError("unclassified Win32 red, retain raw native evidence")
        out["decision"] = "J24W01_SYMLINK_MTIME_REGRESSION_CONFIRMED"
        out["evidence_class"] = "native installed-product negative"
        out["native_error_tail"] = errors[-3000:]
    out["controls"] = {
        "historical": baseline["result"],
        "o167": positive["result"],
        "shared_archive_sha256": archive,
        "donor_source_sha": DONOR,
        "original_untouched_court": O171_BLOB,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("archive", "receipt", "baseline", "positive", "candidate", "court", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    out = {"schema": SCHEMA, "decision": "UNCLASSIFIED"}
    code = 0
    try:
        decide(a, out)
    except Exception as exc:
        code = 1
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["traceback"] = traceback.format_exc()[-5000:]
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k != "traceback"}, sort_keys=True))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
