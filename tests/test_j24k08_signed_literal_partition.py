"""J24K08: same physical projection, different literal arrangement and range bytes.

This is a proof-scope experiment. Structural preflight is not asserted to promise
cryptographic authentication of partial ranges.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import msgpack
import pytest

from cmpct.codec import MAGIC, VERSION, FMAGIC, HDR, FTR, zc, zd, sha, S_VZIP
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

GOLDEN = Path(__file__).parent / "conformance" / "v24-virtual-zip-deflate-mode0.json"


def _err_or_ok(fn):
    try:
        return {"status": "ACCEPT", "value": fn()}
    except Exception as exc:
        return {"status": "REJECT", "exception": type(exc).__name__, "message": str(exc)[:180]}


def test_signed_same_projection_reallocated_literal_boundary(tmp_path):
    row = json.loads(GOLDEN.read_text(encoding="utf-8"))["vector"]
    assert row["archive_sha256"] == "9fa44e064af01a2fdc7402881bb89d9449cbc5de6a26563d05f71b812af0c224"
    original = base64.b64decode(row["archive_base64"], validate=True)
    assert hashlib.sha256(original).hexdigest() == row["archive_sha256"]
    magic, version, flags, ci, ui, body_length, digest = HDR.unpack_from(original)
    assert magic == MAGIC and version == VERSION
    idx_encoded = original[HDR.size:HDR.size + ci]
    decoded = zd(idx_encoded, ui)
    assert sha(decoded) == digest
    base = HDR.size + ci
    body = original[base:base + body_length]
    assert original[base + body_length:base + body_length + ci] == idx_encoded
    assert FTR.unpack_from(original, base + body_length + ci)[-1] == digest
    idx = msgpack.unpackb(decoded, raw=False)
    assert len(idx["recipes"]) == len(idx["files"]) == 1
    f = idx["files"][0]
    assert f[6][0] == S_VZIP
    original_recipe = idx["recipes"][f[6][1]]
    assert original_recipe[1] == [39, 77]
    assert original_recipe[4] == f[4] == row["logical_size"] == 130
    assert original_recipe[2][0][4] == 14 and original_recipe[2][0][2] == 0

    legitimate_path = tmp_path / "control.cmpct"
    legitimate_path.write_bytes(original)
    assert preflight_archive(legitimate_path)["files"] == 1
    with CMPCT(legitimate_path) as good:
        exact = good.read(row["name"])
        assert hashlib.sha256(exact).hexdigest() == row["logical_sha256"]
        assert zipfile.ZipFile(io.BytesIO(exact)).testzip() is None
        assert good.verify() == 1
        assert good.read_range(row["name"], 39, 1) == exact[39:40]

    changed_index = copy.deepcopy(idx)
    recipe = changed_index["recipes"][f[6][1]]
    recipe[1][0] += 1
    recipe[1][1] -= 1
    assert recipe[1] == [40, 76]
    assert sum(recipe[1]) == sum(original_recipe[1]) == idx["blobs"][recipe[0]][1]
    assert sum(recipe[1]) + sum(p[4] for p in recipe[2]) == recipe[4] == 130
    assert changed_index["files"] == idx["files"]
    assert changed_index["blobs"] == idx["blobs"]
    assert recipe[2:] == original_recipe[2:]

    packed_raw = msgpack.packb(changed_index, use_bin_type=True)
    packed = zc(packed_raw, 12)
    new_digest = sha(packed_raw)
    head = HDR.pack(MAGIC, VERSION, flags, len(packed), len(packed_raw), body_length, new_digest)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed), len(packed_raw), 0, new_digest)
    mutant = head + packed + body + packed + footer
    assert sha(zd(packed, len(packed_raw))) == new_digest
    assert mutant[HDR.size + len(packed):HDR.size + len(packed) + body_length] == body
    assert mutant[HDR.size + len(packed) + body_length:-FTR.size] == packed
    assert FTR.unpack_from(mutant, len(mutant) - FTR.size)[-1] == new_digest

    hostile_path = tmp_path / "relocated-literals.cmpct"
    hostile_path.write_bytes(mutant)
    preflight = _err_or_ok(lambda: preflight_archive(hostile_path))
    with CMPCT(hostile_path) as ar:
        full = _err_or_ok(lambda: ar.read(row["name"]))
        verify = _err_or_ok(lambda: ar.verify())
        ranges = {str(off): _err_or_ok(lambda off=off: ar.read_range(row["name"], off, 1))
                  for off in (37, 38, 39, 40, 41, 52, 53, 54)}
    results = []
    for key, r in ranges.items():
        off = int(key)
        if r["status"] == "ACCEPT":
            value = r["value"]
            results.append({"offset": off, "length": len(value), "got": value.hex(),
                            "expected": exact[off:off+1].hex(), "mismatch": value != exact[off:off+1]})
        else:
            results.append({"offset": off, "status": "REJECT", "message": r["message"]})
    receipt = {
        "question": "J24K08", "source_sha": os.environ.get("SOURCE_SHA", "LOCAL"),
        "golden_archive_sha256": hashlib.sha256(original).hexdigest(),
        "reallocated_archive_sha256": hashlib.sha256(mutant).hexdigest(),
        "physical_sha256": hashlib.sha256(body).hexdigest(),
        "original_literals": original_recipe[1],
        "reallocated_literals": recipe[1],
        "logical_size": row["logical_size"],
        "preflight": preflight["status"],
        "whole_read": full["status"], "verify": verify["status"],
        "ranges": results,
    }
    print("J24K08_RECEIPT=" + json.dumps(receipt, sort_keys=True), flush=True)
    assert preflight["status"] == "ACCEPT", receipt
    assert full["status"] == "REJECT" and verify["status"] == "REJECT", receipt
    assert any(r.get("offset") == 39 and r.get("mismatch") and r.get("length") == 1 for r in results), receipt
