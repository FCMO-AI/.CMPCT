"""J24K07: signed STORED/retained VZIP skipped-stream suffix-coordinate court.

Scientific OBSERVATION test, not a product fix. Exactly two previously frozen
Builder-independent r24 vectors; no opportunistic fixture search.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

import msgpack
import pytest

from cmpct.codec import FMAGIC, FTR, HDR, MAGIC, VERSION, S_VZIP, sha, zc, zd
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive


FIXTURES = [
    ("stored", "v24-virtual-zip.json", zipfile.ZIP_STORED, 0),
    ("retained", "v24-virtual-zip-deflate-mode1.json", zipfile.ZIP_DEFLATED, 1),
]
ROOT = Path(__file__).parent / "conformance"


def _golden(case):
    row = json.loads((ROOT / case[1]).read_text(encoding="utf-8"))["vector"]
    physical_wire = base64.b64decode(row["archive_base64"], validate=True)
    assert hashlib.sha256(physical_wire).hexdigest() == row["archive_sha256"]
    magic, revision, flags, ci, ui, physical_len, original_sha = HDR.unpack_from(physical_wire)
    assert magic == MAGIC and revision == VERSION
    compressed = physical_wire[HDR.size:HDR.size + ci]
    decoded = zd(compressed, ui)
    assert sha(decoded) == original_sha
    physical_start = HDR.size + ci
    physical = physical_wire[physical_start:physical_start + physical_len]
    assert physical_wire[physical_start + physical_len:physical_start + physical_len + ci] == compressed
    assert FTR.unpack_from(physical_wire, physical_start + physical_len + ci)[-1] == original_sha
    index = msgpack.unpackb(decoded, raw=False)
    assert len(index["recipes"]) == len(index["files"]) == 1
    file_entry = index["files"][0]
    assert file_entry[6][0] == S_VZIP
    recipe = index["recipes"][file_entry[6][1]]
    assert len(recipe[2]) == 1
    assert len(recipe[1]) == 2
    assert recipe[4] == file_entry[4] == row["logical_size"]
    assert recipe[2][0][1] == case[2] and recipe[2][0][2] == case[3]
    return row, physical_wire, physical, flags, index, recipe


def _signed_mutant(wire, physical, flags, index, delta):
    assert delta in (-1, 1)
    modified = copy.deepcopy(index)
    entry = modified["files"][0]
    recipe = modified["recipes"][entry[6][1]]
    original_csize = recipe[2][0][4]
    assert original_csize > 1
    recipe[2][0][4] = original_csize + delta
    recipe[4] += delta
    entry[4] += delta
    assert entry[4] == recipe[4]
    assert modified["blobs"] == index["blobs"]
    payload = msgpack.packb(modified, use_bin_type=True)
    packed = zc(payload, 12)
    signed = sha(payload)
    header = HDR.pack(MAGIC, VERSION, flags, len(packed), len(payload), len(physical), signed)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed), len(payload), 0, signed)
    altered = header + packed + physical + packed + footer
    assert altered[HDR.size + len(packed):HDR.size + len(packed) + len(physical)] == physical
    assert altered[HDR.size + len(packed) + len(physical):-FTR.size] == packed
    assert FTR.unpack_from(altered, len(altered) - FTR.size)[-1] == signed
    assert sha(zd(packed, len(payload))) == signed
    return altered, original_csize


def _error_or_value(fn):
    try:
        result = fn()
    except Exception as exc:
        return {"status": "REJECT", "exception": type(exc).__name__, "message": str(exc)[:180]}
    return {"status": "ACCEPT", "value": result}


@pytest.mark.parametrize("case", FIXTURES, ids=lambda v: v[0])
@pytest.mark.parametrize("delta", (-1, 1), ids=("minus1", "plus1"))
def test_reauthenticated_nonmode2_skipped_stream_suffix_coordinates(tmp_path, case, delta):
    vector, original_wire, physical, flags, original_index, original_recipe = _golden(case)
    original = tmp_path / "legitimate.cmpct"
    original.write_bytes(original_wire)
    assert preflight_archive(original)["files"] == 1

    with CMPCT(original) as good:
        exact = good.read(vector["name"])
        assert hashlib.sha256(exact).hexdigest() == vector["logical_sha256"]
        assert zipfile.ZipFile(io.BytesIO(exact)).testzip() is None
        assert good.verify() == 1
        assert good.read_range(vector["name"], 0, len(exact)) == exact

    mutated, physical_csize = _signed_mutant(original_wire, physical, flags, original_index, delta)
    path = tmp_path / "reauthenticated-invalid.cmpct"
    path.write_bytes(mutated)
    admission = _error_or_value(lambda: preflight_archive(path))
    assert admission["status"] == "REJECT" and admission["exception"] == "ValidationError", admission
    # Post-first-court adversarial tightening: the strict control must reject for
    # exactly the untrusted csize-to-physical-owner disagreement, not an
    # unrelated syntax/frame issue that would mask a broken experiment.
    cause = ("stored payload" if case[2] == zipfile.ZIP_STORED else
             "retained stream" if case[3] == 1 else "canonical Deflate stream")
    assert cause in admission["message"], (cause, admission)
    suffix_begin = original_recipe[1][0] + physical_csize
    # The preregistered query universe is all one-byte offsets past the
    # skipped stream, within BOTH the original and mutated declared totals.
    # Never select a special post-result witness outside this fixed universe.
    query_start = suffix_begin + 1
    query_stop = min(len(exact), len(exact) + delta)
    assert query_stop > query_start + 2
    probes = []
    whole = None
    verify = None
    opened = False
    try:
        with CMPCT(path) as candidate:
            opened = True
            whole = _error_or_value(lambda: candidate.read(vector["name"]))
            verify = _error_or_value(lambda: candidate.verify())
            for offset in range(query_start, query_stop):
                observed = _error_or_value(lambda offset=offset: candidate.read_range(vector["name"], offset, 1))
                if observed["status"] == "ACCEPT":
                    value = observed["value"]
                    observed = {
                        "status": "ACCEPT",
                        "length": len(value),
                        "hex": value.hex(),
                        "expected_hex": exact[offset:offset + 1].hex(),
                        "byte_mismatch": len(value) == 1 and value != exact[offset:offset + 1],
                    }
                probes.append({"offset": offset, **observed})
    except Exception as exc:
        whole = {"status": "REJECT", "exception": type(exc).__name__, "message": str(exc)[:180]}
    wrong = [p for p in probes if p["status"] == "ACCEPT" and p["byte_mismatch"]]
    receipt = {
        "family": "J24K07", "case": case[0], "delta": delta,
        "original_archive_sha256": hashlib.sha256(original_wire).hexdigest(),
        "original_logical_sha256": vector["logical_sha256"],
        "mutated_archive_sha256": hashlib.sha256(mutated).hexdigest(),
        "physical_sha256": hashlib.sha256(physical).hexdigest(),
        "original_length": len(exact), "mutated_declared_length": len(exact) + delta,
        "original_payload_csize": physical_csize, "declared_payload_csize": physical_csize + delta,
        "preflight": admission["status"], "preflight_cause": admission["message"], "opened": opened,
        "full_read": whole["status"] if whole else "UNMEASURED",
        "verify": verify["status"] if verify else "UNMEASURED",
        "probe_count": len(probes), "wrong_byte_count": len(wrong),
        "first_wrong": wrong[0] if wrong else None,
        "rejected_probes": sum(p["status"] != "ACCEPT" for p in probes),
        "truncated_probes": sum(p["status"] == "ACCEPT" and p["length"] != 1 for p in probes),
        "source_sha": os.getenv("SOURCE_SHA", "LOCAL"),
    }
    print("J24K07_RECEIPT=" + json.dumps(receipt, sort_keys=True), flush=True)
    assert opened, receipt
    assert whole["status"] == "REJECT", receipt
    assert verify["status"] == "REJECT", receipt
    assert len(wrong) > 0, receipt
