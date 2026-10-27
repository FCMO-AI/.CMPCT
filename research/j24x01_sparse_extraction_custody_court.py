"""J24X01 science-only *negative* court against the exact released r24 Reader.

A PASS means the preregistered vulnerability was reproduced; it is NOT evidence
of product correctness. The stock Reader, validator, frozen vector and release law
are not changed. Every archive has valid r24 checksums except the explicitly
declared logical commitment or physical payload perturbation.
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


def error_of(operation):
    try:
        result = operation()
        return {"ok": True, "result": result if isinstance(result, int) else None}
    except Exception as e:
        return {"ok": False, "type": type(e).__name__, "message": str(e)}


def case(directory, label, **flags):
    raw, index, logical, physical_pos = build(**flags)
    archive_path = directory / f"{label}.cmpct"
    archive_path.write_bytes(raw)
    digest0 = hashlib.sha256(raw).hexdigest()
    preflight = error_of(lambda: preflight_archive(archive_path, verify_blob_headers=True))
    assert preflight["ok"], (label, "preflight did not accept the structural control", preflight)
    out_dir = directory / f"dest-{label}"
    out_dir.mkdir()
    output = out_dir / PATH
    output.write_bytes(CANARY)
    original_inode = output.stat().st_ino
    with CMPCT(archive_path) as reader:
        index_hash = reader.by[PATH][5]
        logical_size = reader.by[PATH][4]
        assert index_hash == index["files"][0][5]
        assert logical_size == len(logical)
        read = error_of(lambda: reader.read(PATH))
        verify = error_of(reader.verify)
        extraction = error_of(lambda: reader.extractall(out_dir, metadata=False))
    actual_bytes = output.read_bytes()
    record = {
        "label": label,
        "flags": flags,
        "archive_bytes": len(raw),
        "archive_sha256": digest0,
        "archive_unchanged": hashlib.sha256(archive_path.read_bytes()).hexdigest() == digest0,
        "payload_offset": physical_pos,
        "expected_logical_sha256": index_hash.hex(),
        "intended_bytes_sha256": hashlib.sha256(logical).hexdigest(),
        "preflight": preflight,
        "read": read,
        "verify": verify,
        "extract": extraction,
        "destination_before_sha256": hashlib.sha256(CANARY).hexdigest(),
        "destination_after_sha256": hashlib.sha256(actual_bytes).hexdigest(),
        "destination_after_bytes": len(actual_bytes),
        "destination_inode_preserved": output.stat().st_ino == original_inode,
        "destination_preserved": actual_bytes == CANARY,
        "output_equals_logical": actual_bytes == logical,
    }
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    normalized = lambda b: b.replace(b"\r\n", b"\n")
    reader_path = Path(inspect.getfile(reader_mod)).resolve()
    validator_path = Path(inspect.getfile(val_mod)).resolve()
    provenance = {
        "reader_python_file": str(reader_path),
        "reader_sha256": hashlib.sha256(normalized(reader_path.read_bytes())).hexdigest(),
        "validator_sha256": hashlib.sha256(normalized(validator_path.read_bytes())).hexdigest(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "scientific_only": True,
    }
    with tempfile.TemporaryDirectory(prefix="j24x01-") as tmp:
        root = Path(tmp)
        good = case(root, "control-valid-sparse")
        blob = case(root, "control-unrelated-blob", as_blob=True)
        wrong = case(root, "wrong-logical-digest", wrong_logical_sha=True)
        corrupt = case(root, "corrupt-physical-blob", corrupt_physical=True)

    # Mandatory prospective predictions, not opportunistic success reclassification.
    assert good["read"]["ok"] and good["verify"]["ok"] and good["extract"]["ok"], good
    assert good["output_equals_logical"] and good["archive_unchanged"], good
    assert blob["read"]["ok"] and blob["verify"]["ok"] and blob["extract"]["ok"], blob
    assert blob["output_equals_logical"] and blob["archive_unchanged"], blob
    assert not wrong["read"]["ok"] and not wrong["verify"]["ok"], wrong
    assert wrong["extract"]["ok"] and wrong["output_equals_logical"], wrong
    assert wrong["destination_after_sha256"] != wrong["expected_logical_sha256"], wrong
    assert not corrupt["read"]["ok"] and not corrupt["verify"]["ok"], corrupt
    assert not corrupt["extract"]["ok"], corrupt
    assert not corrupt["destination_preserved"], corrupt
    assert corrupt["archive_unchanged"] and wrong["archive_unchanged"], corrupt
    result = {
        "schema": "j24x01-extraction-custody-negative-v1",
        "classification": "SPARSE_LOGICAL_SHA_UNCHECKED_AND_DESTINATION_DESTROYED_ON_BLOB_FAILURE",
        "research_only": True,
        "source": provenance,
        "cases": [good, blob, wrong, corrupt],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24X01_NEGATIVE_REPRODUCED=YES")
    print("J24X01_COURT_CASES=4")
    print("J24X01_OUTPUT=" + str(args.out))
    for c in result["cases"]:
        print("CASE " + c["label"] + " " + json.dumps({
            "read": c["read"]["ok"], "verify": c["verify"]["ok"],
            "extract": c["extract"]["ok"], "destination_preserved": c["destination_preserved"],
            "output_matches_declared_sha": c["destination_after_sha256"] == c["expected_logical_sha256"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
