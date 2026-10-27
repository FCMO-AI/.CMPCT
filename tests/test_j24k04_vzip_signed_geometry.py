"""J24K04: fully reauthenticated S_VZIP logical/physical geometry falsifier.

This observational court preserves the released Reader/Validator and original independent
golden archives. A green court establishes the predicted defect, not a product fix.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import zipfile

import msgpack
import pytest

from cmpct.codec import HDR, FTR, MAGIC, FMAGIC, VERSION, S_VZIP, sha, zd, zc
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

ROOT = Path(__file__).resolve().parent / "conformance"
GOLDENS = (
    "v24-virtual-zip.json",
    "v24-virtual-zip-deflate-mode1.json",
)


def _mutation(wire: bytes, new_size: int) -> tuple[bytes, dict]:
    """Alter exactly two authenticated logical-size fields, not physical source bytes."""
    magic, revision, flags, ci, ui, physical_len, ih = HDR.unpack_from(wire)
    assert magic == MAGIC and revision == VERSION
    old_index_compressed = wire[HDR.size:HDR.size + ci]
    old_index_bytes = zd(old_index_compressed, ui)
    assert sha(old_index_bytes) == ih
    physical_start = HDR.size + ci
    physical_end = physical_start + physical_len
    physical = wire[physical_start:physical_end]
    assert len(physical) == physical_len
    assert wire[physical_end:physical_end + ci] == old_index_compressed
    footer = FTR.unpack_from(wire, physical_end + ci)
    assert footer[0] == FMAGIC and footer[-1] == ih
    index = msgpack.unpackb(old_index_bytes, raw=False)
    assert len(index["files"]) == len(index["recipes"]) == 1
    row = index["files"][0]
    assert row[6][0] == S_VZIP
    rid = row[6][1]
    recipe = index["recipes"][rid]
    assert row[4] == recipe[4] == new_size - 1
    before = copy.deepcopy(index)
    row[4] = new_size
    recipe[4] = new_size
    # Demonstrate no other semantic index field was edited.
    restored = copy.deepcopy(index)
    restored["files"][0][4] -= 1
    restored["recipes"][rid][4] -= 1
    assert restored == before
    new_index_bytes = msgpack.packb(index, use_bin_type=True)
    new_index_compressed = zc(new_index_bytes, 12)
    new_hash = sha(new_index_bytes)
    new_header = HDR.pack(MAGIC, VERSION, flags, len(new_index_compressed),
                          len(new_index_bytes), physical_len, new_hash)
    new_footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(new_index_compressed),
                          len(new_index_bytes), 0, new_hash)
    tampered = new_header + new_index_compressed + physical + new_index_compressed + new_footer
    # Independently check all physical bytes and both authenticated index copies.
    assert tampered[HDR.size + len(new_index_compressed):
                    HDR.size + len(new_index_compressed) + physical_len] == physical
    assert sha(zd(tampered[HDR.size:HDR.size + len(new_index_compressed)],
                  len(new_index_bytes))) == new_hash
    assert tampered[-FTR.size - len(new_index_compressed):-FTR.size] == new_index_compressed
    return tampered, {
        "physical_sha256": hashlib.sha256(physical).hexdigest(),
        "original_index_sha256": ih.hex(),
        "mutated_index_sha256": new_hash.hex(),
        "original_logical_size": new_size - 1,
        "mutated_logical_size": new_size,
        "mutated_archive_sha256": hashlib.sha256(tampered).hexdigest(),
    }


@pytest.mark.parametrize("fixture", GOLDENS, ids=("stored", "retained-deflate"))
def test_fully_signed_vzip_declared_size_exceeds_physical_reconstruction(tmp_path, fixture):
    golden = json.loads((ROOT / fixture).read_text(encoding="utf-8"))["vector"]
    wire = __import__("base64").b64decode(golden["archive_base64"])
    assert hashlib.sha256(wire).hexdigest() == golden["archive_sha256"]
    name = golden["name"]
    normal = tmp_path / "normal.cmpct"
    normal.write_bytes(wire)
    assert preflight_archive(normal)["files"] == 1
    with CMPCT(normal) as reader:
        original = reader.read(name)
        assert len(original) == golden["logical_size"]
        assert hashlib.sha256(original).hexdigest() == golden["logical_sha256"]
        assert zipfile.ZipFile(io.BytesIO(original)).testzip() is None
        assert reader.verify() == 1
        assert reader.read_range(name, len(original) - 1, 1) == original[-1:]
        with pytest.raises(ValueError):
            reader.read_range(name, len(original), 1)

    mutant_bytes, receipt = _mutation(wire, len(original) + 1)
    mutant = tmp_path / "fully-signed-oversize.cmpct"
    mutant.write_bytes(mutant_bytes)
    receipt["fixture"] = fixture
    receipt["original_archive_sha256"] = golden["archive_sha256"]
    receipt["preflight"] = "UNMEASURED"
    receipt["full_read"] = "UNMEASURED"
    receipt["selective"] = "UNMEASURED"
    try:
        preflight_archive(mutant)
        receipt["preflight"] = "ACCEPT"
    except Exception as exc:
        receipt["preflight"] = "REJECT:" + type(exc).__name__
    with CMPCT(mutant) as reader:
        try:
            reader.read(name)
            receipt["full_read"] = "ACCEPT"
        except Exception as exc:
            receipt["full_read"] = "REJECT:" + type(exc).__name__
        try:
            out = reader.read_range(name, len(original), 1)
            receipt["selective"] = "ACCEPT:" + out.hex()
            receipt["returned_bytes"] = len(out)
        except Exception as exc:
            receipt["selective"] = "REJECT:" + type(exc).__name__
    print("J24K04_OBSERVED=" + json.dumps(receipt, sort_keys=True), flush=True)
    # A green research court means the preregistered defect was observed.
    assert receipt["preflight"] == "ACCEPT"
    assert receipt["full_read"].startswith("REJECT:")
    assert receipt["selective"] == "ACCEPT:"
    assert receipt["returned_bytes"] == 0
