"""J24X02 positive portability/custody court on the existing verified sparse owner candidate.

Compare historical and candidate helper on independently signed revision-24 bytes.
A PASS is a scoped candidate verification, not a release or performance benchmark.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import tempfile

import msgpack

import cmpct.reader as reader_mod
import cmpct.validation as val_mod
from cmpct.codec import (
    MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
    CODEC_RAW, K_FILE, S_SPARSE, S_BLOB, zc, sha,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

PAYLOAD = b"ABCD"
LOGICAL = b"\0" * 4 + PAYLOAD + b"\0" * 4
PATH = "sparse.bin"
CANARY = b"ORIGINAL_DESTINATION_SHALL_SURVIVE_FAILURE" * 3


def build(*, wrong_logical_sha=False, corrupt_physical=False, as_blob=False):
    """Create an authenticated root-versioned r24 archive, independent of Builder."""
    storage = [S_BLOB, 0] if as_blob else [S_SPARSE, [[4, 4, [0]]]]
    logical = PAYLOAD if as_blob else LOGICAL
    expected_digest = sha(b"NOT_THE_SPARSE_FILE") if wrong_logical_sha else sha(logical)
    index = {
        "v": VERSION,
        "files": [[PATH, K_FILE, 0o644, 946684800000000000,
                   len(logical), expected_digest, storage]],
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None, "fsmeta": {},
    }
    idx = msgpack.packb(index, use_bin_type=True)
    enc = zc(idx, 12)
    digest = sha(idx)
    rec = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xffffffff, sha(PAYLOAD)
    ) + PAYLOAD
    raw = (
        HDR.pack(MAGIC, VERSION, 0, len(enc), len(idx), len(rec), digest)
        + enc + rec + enc
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(enc), len(idx), 0, digest)
    )
    blob_payload_offset = HDR.size + len(enc) + BHDR.size
    if corrupt_physical:
        changed = bytearray(raw)
        assert changed[blob_payload_offset] == PAYLOAD[0]
        changed[blob_payload_offset] ^= 0x01
        raw = bytes(changed)
    return raw, index, logical, blob_payload_offset



import contextlib
import sys
import cmpct.sparse_extract as sparse_mod

@contextlib.contextmanager
def mode_api(mode):
    available = hasattr(os, "fchmod")
    saved = getattr(os, "fchmod", None)
    def fail(exc):
        def raise_exc(*a, **k):
            raise exc
        return raise_exc
    if mode == "absent":
        if available:
            delattr(os, "fchmod")
    elif mode == "oserror":
        os.fchmod = fail(OSError("synthetic optional mode error"))
    elif mode == "valueerror":
        os.fchmod = fail(ValueError("synthetic programming error"))
    try:
        yield
    finally:
        if available:
            os.fchmod = saved
        elif hasattr(os, "fchmod"):
            delattr(os, "fchmod")


@contextlib.contextmanager
def alternative_helper(fn):
    saved = sparse_mod.write_sparse_verified
    if fn is not None:
        sparse_mod.write_sparse_verified = fn
    try:
        yield
    finally:
        sparse_mod.write_sparse_verified = saved


def run_case(root, label, *, mode="real", baseline=None,
             wrong_logical_sha=False, corrupt_physical=False, as_blob=False):
    raw, index, logical, _ = build(wrong_logical_sha=wrong_logical_sha,
                                  corrupt_physical=corrupt_physical, as_blob=as_blob)
    arc = root / (label + ".cmpct")
    arc.write_bytes(raw)
    archive_sha = hashlib.sha256(raw).hexdigest()
    dest = root / (label + "-dest")
    dest.mkdir()
    output = dest / PATH
    output.write_bytes(CANARY)
    inode_before = output.stat().st_ino
    preflight = preflight_archive(arc, verify_blob_headers=True)
    with CMPCT(arc) as reader:
        assert reader.by[PATH][5] == index["files"][0][5]
        def invoke():
            with alternative_helper(baseline), mode_api(mode):
                reader.extractall(dest, metadata=False)
        try:
            invoke()
            result = {"ok": True, "type": None, "message": None}
        except Exception as exc:
            result = {"ok": False, "type": type(exc).__name__, "message": str(exc)}
    after = output.read_bytes()
    staged = sorted(p.name for p in dest.iterdir() if p.name != PATH)
    record = {"case": label, "mode_api": mode, "result": result,
              "logical_match": after == logical,
              "canary_preserved": after == CANARY,
              "inode_preserved": output.stat().st_ino == inode_before,
              "staged_leftovers": staged,
              "archive_unchanged": hashlib.sha256(arc.read_bytes()).hexdigest() == archive_sha,
              "output_sha256": hashlib.sha256(after).hexdigest(),
              "expected_sha256": index["files"][0][5].hex(),
              "archive_bytes": len(raw),
              "preflight_present": preflight is not None}
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--base-helper", required=True, type=Path)
    args = p.parse_args()
    source = args.base_helper.read_text()
    assert "os.fchmod(fd, mode or 0o666)" in source
    # Load the actual previous owner implementation without rebuilding the fixture.
    namespace = {"__name__": "_cmpct_previous_sparse_helper"}
    exec(compile(source, str(args.base_helper), "exec"), namespace)
    baseline = namespace["write_sparse_verified"]
    reader_path = Path(inspect.getfile(reader_mod)).resolve()
    helper_path = Path(inspect.getfile(sparse_mod)).resolve()
    validator_path = Path(inspect.getfile(val_mod)).resolve()
    norm = lambda b: b.replace(b"\r\n", b"\n")
    original_api_available = hasattr(os, "fchmod")
    with tempfile.TemporaryDirectory(prefix="j24x02-") as td:
        root = Path(td)
        records = [
            run_case(root, "historical-absent-api", mode="absent", baseline=baseline),
            run_case(root, "candidate-absent-api", mode="absent"),
            run_case(root, "candidate-platform-default"),
            run_case(root, "candidate-mode-oserror", mode="oserror"),
            run_case(root, "candidate-mode-valueerror", mode="valueerror"),
            run_case(root, "candidate-wrong-logical-sha", wrong_logical_sha=True),
            run_case(root, "candidate-corrupt-physical", corrupt_physical=True),
            run_case(root, "control-unrelated-blob", as_blob=True),
        ]
    lookup = {x["case"]: x for x in records}
    historical = lookup["historical-absent-api"]
    assert not historical["result"]["ok"] and historical["result"]["type"] == "AttributeError", historical
    assert historical["canary_preserved"] and not historical["staged_leftovers"], historical
    for key in ["candidate-absent-api", "candidate-platform-default",
                "candidate-mode-oserror", "control-unrelated-blob"]:
        r = lookup[key]
        assert r["result"]["ok"] and r["logical_match"] and not r["staged_leftovers"], r
        assert r["output_sha256"] == r["expected_sha256"], r
    for key, error in [("candidate-mode-valueerror", "ValueError"),
                       ("candidate-wrong-logical-sha", "OSError"),
                       ("candidate-corrupt-physical", "OSError")]:
        r = lookup[key]
        assert not r["result"]["ok"], r
        assert error in (r["result"]["type"], "IOError"), r
        assert r["canary_preserved"] and r["inode_preserved"], r
        assert not r["staged_leftovers"] and r["archive_unchanged"], r
    result = {"schema": "j24x02-sparse-fchmod-positive-v1",
              "classification": "CANDIDATE_SPARSE_PORTABILITY_AND_CUSTODY_PASS",
              "platform": platform.platform(), "python": platform.python_version(),
              "fchmod_available": original_api_available,
              "reader_sha256": hashlib.sha256(norm(reader_path.read_bytes())).hexdigest(),
              "helper_sha256": hashlib.sha256(norm(helper_path.read_bytes())).hexdigest(),
              "validator_sha256": hashlib.sha256(norm(validator_path.read_bytes())).hexdigest(),
              "old_helper_sha256": hashlib.sha256(norm(args.base_helper.read_bytes())).hexdigest(),
              "source_head": os.environ.get("HEAD_SHA"),
              "cases": records}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24X02_PORTABILITY_CUSTODY_PASS=YES")
    print("J24X02_CASES=" + str(len(records)))
    print("J24X02_FCHMOD_NATIVE=" + str(original_api_available))
    for r in records:
        print("CASE " + r["case"] + " " + json.dumps({"ok": r["result"]["ok"],
            "error": r["result"]["type"], "exact": r["logical_match"],
            "canary": r["canary_preserved"], "leftovers": r["staged_leftovers"]}))
    print("J24X02_OUTPUT=" + str(args.out))


if __name__ == "__main__":
    main()
