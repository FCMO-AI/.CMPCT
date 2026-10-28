"""J24C07c: genuine signed regenerated Deflate mode2 controls (prospectively scoped).

The frozen mode1 golden carries a zlib-level-6 compressed stream which the
raw member independently reproduces byte-for-byte. Only mode/ref index fields
change for a valid mode2 control; physical archive blobs never change.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
from pathlib import Path
import zipfile
import zlib

import msgpack
import pytest

from cmpct.codec import FMAGIC, FTR, HDR, MAGIC, VERSION, sha, zd, zc
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive


GOLDEN = Path(__file__).with_name("conformance") / "v24-virtual-zip-deflate-mode1.json"


def mode2_wire(extra_declared_bytes: int):
    assert extra_declared_bytes in (0, 1)
    vector = json.loads(GOLDEN.read_text(encoding="utf-8"))["vector"]
    archived = base64.b64decode(vector["archive_base64"], validate=True)
    assert len(archived) == 762
    assert hashlib.sha256(archived).hexdigest() == (
        "842896d0140844841e02b2c882ca4f81efda16771caacea6248787fe98273573"
    )
    magic, revision, flags, cindex, uindex, physical_len, digest = HDR.unpack_from(archived)
    assert magic == MAGIC and revision == VERSION
    packed = archived[HDR.size:HDR.size + cindex]
    original_index = zd(packed, uindex)
    assert sha(original_index) == digest
    body = archived[HDR.size + cindex:HDR.size + cindex + physical_len]
    assert archived[HDR.size + cindex + physical_len:
                    HDR.size + 2 * cindex + physical_len] == packed
    index = msgpack.unpackb(original_index, raw=False)
    assert len(index["recipes"]) == len(index["files"]) == 1
    recipe = index["recipes"][0]
    payload = recipe[2][0]
    raw_ref, method, stream_mode, stream_ref, compressed_size, level = payload
    assert method == 8 and stream_mode == 1 and compressed_size == 14 and level == 6
    assert recipe[4] == vector["logical_size"] == 130
    assert recipe[1] == [39, 77]

    # The Base64 fixture contains a CMPCT container, not a ZIP. The first
    # hosted court exposed this instrument error before testing the candidate.
    # Preserve the preregistered SHA and Deflate bytes rather than weakening
    # the test by treating CMPCT bytes as a native ZIP.
    member = b"hello-cmpct\n"
    assert len(member) == vector["member"]["logical_size"] == 12
    assert hashlib.sha256(member).hexdigest() == vector["member"]["logical_sha256"]
    compressor = zlib.compressobj(level, zlib.DEFLATED, -15)
    independent_stream = compressor.compress(member) + compressor.flush()
    assert len(independent_stream) == compressed_size
    assert independent_stream.hex() == vector["member"]["exact_deflate_hex"]

    # The existing physical stream blob is now deliberately unused. The original
    # raw blob becomes the mode2 stream input, with the same wire bytes regenerated.
    payload[2] = 2
    payload[3] = raw_ref
    payload[4] += extra_declared_bytes
    recipe[4] += extra_declared_bytes
    index["files"][0][4] += extra_declared_bytes
    encoded = msgpack.packb(index, use_bin_type=True)
    next_packed = zc(encoded, 12)
    next_digest = sha(encoded)
    first = HDR.pack(MAGIC, VERSION, flags, len(next_packed), len(encoded),
                     physical_len, next_digest)
    last = FTR.pack(FMAGIC, 0, 1, 0, 0, len(next_packed), len(encoded), 0, next_digest)
    mutated = first + next_packed + body + next_packed + last
    assert mutated[len(first):len(first) + len(next_packed)] == next_packed
    assert sha(zd(next_packed, len(encoded))) == next_digest
    assert body == archived[HDR.size + cindex:HDR.size + cindex + physical_len]
    return vector, archived, mutated, body


def test_valid_regenerated_mode2_is_exact_and_strictly_admitted(tmp_path: Path):
    vec, original, wire, physical = mode2_wire(0)
    path = tmp_path / "positive-mode2.cmpct"
    path.write_bytes(wire)
    assert preflight_archive(path)["files"] == 1
    with CMPCT(path) as ar:
        result = ar.read(vec["name"])
        assert hashlib.sha256(result).hexdigest() == vec["logical_sha256"]
        assert ar.verify() == 1
        with zipfile.ZipFile(io.BytesIO(result)) as z:
            assert z.testzip() is None
            assert z.read(vec["member"]["name"]) == b"hello-cmpct\n"
        for begin in (0, 1, 35, 42, 50, 100, 129, 130):
            for length in (0, min(1, 130 - begin), 130 - begin):
                assert ar.read_range(vec["name"], begin, length) == result[begin:begin + length]
    print("J24C07C_VALID_MODE2_PASS="+json.dumps({
        "signed_archive_sha256":hashlib.sha256(wire).hexdigest(),
        "physical_sha256":hashlib.sha256(physical).hexdigest(),
        "logical_sha256":vec["logical_sha256"],
        "original_sha256":hashlib.sha256(original).hexdigest(),
    },sort_keys=True),flush=True)


def test_mode2_size_lie_requires_runtime_rejection_not_fake_preflight_proof(tmp_path: Path):
    vec, original, wire, physical = mode2_wire(1)
    path = tmp_path / "invalid-mode2.cmpct"
    path.write_bytes(wire)
    # Mode2 compressed length cannot be established from authenticated raw usize.
    # Passing structural preflight is an explicitly preserved limitation.
    assert preflight_archive(path)["files"] == 1
    with CMPCT(path) as ar:
        with pytest.raises(IOError, match="virtual ZIP compressed-stream size mismatch"):
            ar.read(vec["name"])
        with pytest.raises(IOError, match="virtual ZIP selective reconstruction length mismatch"):
            ar.read_range(vec["name"], vec["logical_size"], 1)
    print("J24C07C_MODE2_SIGNED_PRECHECK_LIMIT_RUNTIME_FAILCLOSED="+json.dumps({
        "signed_archive_sha256":hashlib.sha256(wire).hexdigest(),
        "physical_sha256":hashlib.sha256(physical).hexdigest(),
        "declared_logical_bytes":vec["logical_size"] + 1,
        "true_logical_bytes":vec["logical_size"],
    },sort_keys=True),flush=True)
