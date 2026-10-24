"""Authenticated-index hostile S_PACK conformance through the real Rust ABI.

This extends the independent fixed-byte PR #307 court with *re-signed* index
mutations, never corrupted checksums. It does not import CMPCT's Builder,
Reader, codec or Python preflight as an oracle.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import tempfile
from pathlib import Path

import msgpack

from conformance.generate_v24_pack_golden import FTR, FMAGIC, HDR, sha256, zstd_codec
from native_pack_golden_abi import GOLDEN, load_native, read_native


def authenticated_mutation(wire: bytes, change) -> tuple[bytes, dict]:
    """Change precisely one logical tuple, then authenticate both index copies.

    Leave the physical blob *byte-identical* to the trusted fixture so a
    rejection must come from metadata/structural bounds rather than payload
    corruption, a mismatched header hash or a broken fallback footer.
    """
    compress, decompress = zstd_codec()
    magic, revision, flags, ci, ui, data_span, original_digest = HDR.unpack_from(wire)
    assert magic == b"CMPCT24\0" and revision == 24
    original_index = decompress(wire[HDR.size:HDR.size + ci], ui)
    assert sha256(original_index) == original_digest
    index = msgpack.unpackb(original_index, raw=False, strict_map_key=False)
    assert len(index["blobs"]) == 1

    target = next(row for row in index["files"] if row[0] == "omega.bin")
    assert target[6][0] == 4 and target[6][1] == 0
    assert target[4] == target[6][3] and target[4] > 1
    change(target, index)

    rewritten = msgpack.packb(index, use_bin_type=True)
    assert rewritten != original_index
    encoded = compress(rewritten)
    digest = sha256(rewritten)
    physical = wire[HDR.size + ci:HDR.size + ci + data_span]
    assert len(physical) == data_span

    tampered = (
        HDR.pack(magic, revision, flags, len(encoded), len(rewritten), data_span, digest)
        + encoded + physical + encoded
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(rewritten), 0, digest)
    )
    # A self-consistent header and both authenticated indexes, not a bad CRC
    # or archive truncation, must reach the native parser's storage checks.
    _m, _v, _f, new_ci, new_ui, new_span, new_sha = HDR.unpack_from(tampered)
    assert (new_ci, new_ui, new_span, new_sha) == (
        len(encoded), len(rewritten), data_span, digest
    )
    assert tampered[HDR.size + new_ci:HDR.size + new_ci + new_span] == physical
    assert tampered[-FTR.size - new_ci:-FTR.size] == encoded
    assert FTR.unpack_from(tampered, len(tampered) - FTR.size)[-1] == digest
    assert msgpack.unpackb(decompress(encoded, new_ui), raw=False) == index
    return tampered, index


def hostile_changes(blob_size: int):
    """Distinct S_PACK invalidities; each should fail at native open."""
    return (
        ("past-blob-boundary",
         lambda row, idx: row[6].__setitem__(2, blob_size - row[4] + 1)),
        ("offset-u64-overflow",
         lambda row, idx: row[6].__setitem__(2, (1 << 64) - 1)),
        ("negative-offset",
         lambda row, idx: row[6].__setitem__(2, -1)),
        ("missing-blob",
         lambda row, idx: row[6].__setitem__(1, len(idx["blobs"]))),
        ("slice-size-disagrees-with-file",
         lambda row, idx: row[6].__setitem__(3, row[4] + 1)),
        ("negative-slice-size",
         lambda row, idx: row[6].__setitem__(3, -1)),
        ("noninteger-blob-index",
         lambda row, idx: row[6].__setitem__(1, "0")),
    )


def main() -> None:
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert {v["physical_codec"] for v in manifest["vectors"]} == {0, 1}
    lib = load_native()
    verified = 0
    with tempfile.TemporaryDirectory(prefix="cmpct-pack-index-adversarial-") as td:
        root = Path(td)
        for vector in manifest["vectors"]:
            wire = base64.b64decode(vector["archive_base64"], validate=True)
            assert len(wire) == vector["archive_bytes"]
            assert hashlib.sha256(wire).hexdigest() == vector["archive_sha256"]
            normal = root / f"{vector['name']}-unaltered.cmpct"
            normal.write_bytes(wire)

            # Positive guard: no false success from a broken library or path.
            handle = ctypes.c_void_p()
            assert lib.cmpct_open(str(normal).encode(), ctypes.byref(handle)) == 0
            try:
                assert lib.cmpct_entry_count(handle) == 4
                # The sorted golden index starts with alpha-copy.txt.
                expected = bytes.fromhex(vector["files"]["alpha-copy.txt"]["hex"])
                status, actual = read_native(lib, handle, 0, 0, len(expected))
                assert status == 0 and actual == expected
            finally:
                lib.cmpct_close(handle)

            for label, change in hostile_changes(vector["packed_blob_uncompressed_bytes"]):
                invalid, parsed = authenticated_mutation(wire, change)
                assert len(parsed["blobs"]) == 1
                destination = root / f"{vector['name']}-{label}.cmpct"
                destination.write_bytes(invalid)
                bad_handle = ctypes.c_void_p()
                status = lib.cmpct_open(str(destination).encode(), ctypes.byref(bad_handle))
                if bad_handle.value:
                    lib.cmpct_close(bad_handle)
                assert status != 0, (
                    vector["name"], label,
                    "native accepted a fully authenticated but invalid PACK tuple"
                )
                verified += 1
    assert verified == 14, verified
    print(f"PASS: {verified}/14 authenticated malformed S_PACK indexes rejected by native ABI")


if __name__ == "__main__":
    main()
