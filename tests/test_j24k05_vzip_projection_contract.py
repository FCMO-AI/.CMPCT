"""J24K05: product-candidate VZIP strict geometry + complete selective-range contract.

Consumes three independently frozen revision-24 archives. Does not alter historical
J24K04 observational test, which intentionally expects the vulnerable baseline.
"""
from __future__ import annotations

import base64
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
from cmpct.validation import preflight_archive, ValidationError

GOLDENS = (
    "v24-virtual-zip.json",
    "v24-virtual-zip-deflate-mode0.json",
    "v24-virtual-zip-deflate-mode1.json",
)
ROOT = Path(__file__).resolve().parent / "conformance"


def golden(name):
    row = json.loads((ROOT / name).read_text(encoding="utf-8"))["vector"]
    wire = base64.b64decode(row["archive_base64"])
    assert hashlib.sha256(wire).hexdigest() == row["archive_sha256"]
    return row, wire


def reauthenticated(wire: bytes, mutation: str) -> tuple[bytes, dict]:
    """Rebuild both authenticated index copies, preserving every physical byte."""
    magic, rev, flags, ci, ui, physical_len, original_hash = HDR.unpack_from(wire)
    assert (magic, rev) == (MAGIC, VERSION)
    original_compressed = wire[HDR.size:HDR.size + ci]
    raw = zd(original_compressed, ui)
    assert sha(raw) == original_hash
    start = HDR.size + ci
    physical = wire[start:start + physical_len]
    assert wire[start + physical_len:start + physical_len + ci] == original_compressed
    assert FTR.unpack_from(wire, start + physical_len + ci)[-1] == original_hash
    original_index = msgpack.unpackb(raw, raw=False)
    index = copy.deepcopy(original_index)
    assert len(index["files"]) == len(index["recipes"]) == 1
    file = index["files"][0]
    assert file[6][0] == S_VZIP
    recipe = index["recipes"][file[6][1]]
    assert file[4] == recipe[4]
    if mutation == "declared_plus":
        file[4] += 1
        recipe[4] += 1
    elif mutation == "declared_minus":
        file[4] -= 1
        recipe[4] -= 1
    elif mutation == "skeleton_plus":
        recipe[1][0] += 1
        file[4] += 1
        recipe[4] += 1
    elif mutation == "payload_plus":
        recipe[2][0][4] += 1
        file[4] += 1
        recipe[4] += 1
    else:
        raise AssertionError("unknown mutation")
    assert index["blobs"] == original_index["blobs"]
    assert index["files"][0][:4] == original_index["files"][0][:4]
    assert index["recipes"][0][:1] == original_index["recipes"][0][:1]
    encoded_index = msgpack.packb(index, use_bin_type=True)
    packed_index = zc(encoded_index, 12)
    digest = sha(encoded_index)
    head = HDR.pack(MAGIC, VERSION, flags, len(packed_index), len(encoded_index),
                    physical_len, digest)
    tail = FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed_index), len(encoded_index), 0, digest)
    mutated = head + packed_index + physical + packed_index + tail
    # Verify the alternate location has exactly the same authenticated bytes.
    mutstart = HDR.size + len(packed_index)
    assert mutated[mutstart:mutstart + physical_len] == physical
    assert mutated[mutstart + physical_len:mutstart + physical_len + len(packed_index)] == packed_index
    assert sha(zd(packed_index, len(encoded_index))) == digest
    return mutated, {
        "mutation": mutation,
        "physical_sha256": hashlib.sha256(physical).hexdigest(),
        "source_sha256": hashlib.sha256(wire).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated).hexdigest(),
    }


@pytest.mark.parametrize("name", GOLDENS, ids=("stored", "canonical-deflate", "retained-deflate"))
def test_golden_positive_and_exact_range(tmp_path, name):
    ref, wire = golden(name)
    path = tmp_path / "original.cmpct"
    path.write_bytes(wire)
    assert preflight_archive(path)["files"] == 1
    with CMPCT(path) as reader:
        raw = reader.read(ref["name"])
        assert len(raw) == ref["logical_size"]
        assert hashlib.sha256(raw).hexdigest() == ref["logical_sha256"]
        assert zipfile.ZipFile(io.BytesIO(raw)).testzip() is None
        assert reader.verify() == 1
        for start in (0, 1, len(raw) // 2, len(raw) - 1, len(raw)):
            for length in (0, min(1, len(raw) - start), len(raw) - start):
                assert reader.read_range(ref["name"], start, length) == raw[start:start+length]


@pytest.mark.parametrize("name", GOLDENS, ids=("stored", "canonical-deflate", "retained-deflate"))
@pytest.mark.parametrize("mutation", (
    "declared_plus", "declared_minus", "skeleton_plus", "payload_plus",
))
def test_fully_signed_invalid_geometry_rejected(tmp_path, name, mutation):
    ref, wire = golden(name)
    hostile, receipt = reauthenticated(wire, mutation)
    path = tmp_path / (mutation + ".cmpct")
    path.write_bytes(hostile)
    with pytest.raises(ValidationError):
        preflight_archive(path)
    print("J24K05_PREFLIGHT_REJECT=" + json.dumps({
        **receipt, "fixture": name, "outcome": "REJECT"
    }, sort_keys=True), flush=True)


@pytest.mark.parametrize("name", GOLDENS, ids=("stored", "canonical-deflate", "retained-deflate"))
def test_no_silent_selective_short_read_even_without_preflight(tmp_path, name):
    ref, wire = golden(name)
    hostile, receipt = reauthenticated(wire, "declared_plus")
    path = tmp_path / "signed-oversize.cmpct"
    path.write_bytes(hostile)
    with CMPCT(path) as reader:
        # A Reader open currently does not run strict preflight; the representation
        # primitive itself must refuse to promise a byte it cannot reconstruct.
        with pytest.raises(IOError, match="virtual ZIP selective reconstruction length mismatch"):
            reader.read_range(ref["name"], ref["logical_size"], 1)
    print("J24K05_SHORT_READ_REJECT=" + json.dumps(receipt, sort_keys=True), flush=True)


def test_mode2_metadata_does_not_pretend_raw_size_equals_compressed_size():
    from cmpct.validation import _validate_recipe, ParserLimits
    # Component-only negative-control: canonical mode 2 regenerates Deflate;
    # the metadata verifier cannot derive compressed-byte size from raw usize.
    blobs = [
        [0, 10, 10, 0, 0],  # 10 skeleton literal bytes
        [10, 100, 100, 0, 0],  # 100 raw bytes, compressed length unknown at this stage
    ]
    recipe = [0, [5, 5], [[1, 8, 2, 1, 11, 6]], bytes(32), 21, 0]
    _validate_recipe(recipe, blobs, ParserLimits(), 0)
    recipe[4] += 1
    with pytest.raises(ValidationError, match="physical projection"):
        _validate_recipe(recipe, blobs, ParserLimits(), 0)
