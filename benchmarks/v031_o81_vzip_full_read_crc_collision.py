"""O81: reproducible full-read CRC32 collision oracle, not a product patch.

A valid VZIP source ZIP and a second valid ZIP share CRC32 and length, but differ in
SHA-256. Tests the actual installed CMPCT.read()/verify() contract independently.
The staged decoded-blob oracle is always attempted; RAW-blob physical tamper is
attempted only when the actual Builder emits a RAW skeleton.
"""
from __future__ import annotations

import binascii
import hashlib
import io
import json
import random
import shutil
import tempfile
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import BHDR, CODEC_RAW, S_VZIP
from cmpct.reader import CMPCT


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def crc(blob):
    return binascii.crc32(blob) & 0xffffffff


def same_crc_mutation(source: bytes, flip: int, patch: int) -> bytes:
    """Solve the exact CRC32 linear compensation, without using a found collision."""
    out = bytearray(source)
    out[flip] ^= 1
    target = crc(source) ^ crc(out)
    intermediate = crc(out)
    basis = {}
    for bit in range(32):
        trial = bytearray(out)
        trial[patch + bit // 8] ^= 1 << (bit % 8)
        vector = crc(trial) ^ intermediate
        mask = 1 << bit
        for pivot in sorted(basis, reverse=True):
            if vector & (1 << pivot):
                old_vector, old_mask = basis[pivot]
                vector ^= old_vector
                mask ^= old_mask
        if vector:
            basis[vector.bit_length() - 1] = (vector, mask)
    combination = 0
    for pivot in range(31, -1, -1):
        if target & (1 << pivot):
            if pivot not in basis:
                raise AssertionError("CRC correction matrix not invertible")
            vector, mask = basis[pivot]
            target ^= vector
            combination ^= mask
    if target:
        raise AssertionError("CRC correction did not close")
    for bit in range(32):
        if combination & (1 << bit):
            out[patch + bit // 8] ^= 1 << (bit % 8)
    result = bytes(out)
    assert result != source and len(result) == len(source)
    assert crc(result) == crc(source) and sha(result) != sha(source)
    return result


def make_sources():
    buf = io.BytesIO()
    comment = random.Random(810_025).randbytes(25000)
    original_member = bytes(range(256)) * 3
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        z.writestr("a", original_member, compress_type=zipfile.ZIP_STORED)
        z.comment = comment
    source = buf.getvalue()
    mutated = same_crc_mutation(source, len(source) - len(comment) + 42, len(source) - 8)
    for data in (source, mutated):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None
            assert z.namelist() == ["a"]
            assert z.read("a") == original_member
    assert source[:-len(comment)] == mutated[:-len(comment)]
    return source, mutated, len(comment)


def read_candidate(reader, skref, sk_modified):
    old = reader._blob
    reader._blob = lambda index: sk_modified if index == skref else old(index)
    try:
        result = reader.read("sample.zip")
        rejected = False
        try:
            reader.verify()
        except IOError:
            rejected = True
        return result, rejected
    finally:
        reader._blob = old


def main():
    source, mutated, comment_len = make_sources()
    report = {
        "schema": "cmpct-o81-full-read-crc-collision-v1",
        "source_base": "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b",
        "original_reader_git_blob": "e716233403dabd0966863c45635e18fa5ac6afb8",
        "source_zip_size": len(source),
        "original_zip_sha256": sha(source),
        "mutated_zip_sha256": sha(mutated),
        "equal_complete_zip_crc32": crc(source) == crc(mutated),
        "same_logical_zip_members": True,
        "physical_archive_test": "not_applicable",
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-o81-") as temp:
        root = Path(temp) / "source"
        root.mkdir()
        (root / "sample.zip").write_bytes(source)
        archive = Path(temp) / "original.cmpct"
        Builder(root, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            row = reader.by["sample.zip"]
            if row[6][0] != S_VZIP:
                raise AssertionError("Invalid instrument: Builder did not emit authentic VZIP")
            assert reader.read("sample.zip") == source
            assert reader.verify() == 1
            recipe = reader.recipes[row[6][1]]
            skref = recipe[0]
            skeleton = reader._blob(skref)
            assert skeleton[-comment_len:] == source[-comment_len:]
            sk_modified = skeleton[:-comment_len] + mutated[-comment_len:]
            assert len(sk_modified) == len(skeleton)
            assert crc(sk_modified) == crc(skeleton)
            assert sha(sk_modified) != sha(skeleton)
            assert bytes(recipe[3]) == bytes.fromhex(sha(source))
            assert bytes(row[5]) == bytes.fromhex(sha(source))
            report["skeleton_crc_equal"] = True
            report["archive_bytes"] = archive.stat().st_size
            report["skeleton_storage_codec"] = reader.blobs[skref][3]
            reader.vcache.clear()
            altered, rejected = read_candidate(reader, skref, sk_modified)
            report["decoded_oracle_read_returned_changed_zip"] = altered == mutated
            report["decoded_oracle_verify_rejected"] = rejected
            # A stronger test uses actual independently copied archive bytes when
            # Builder selected RAW skeleton. No monkeypatch / index edit on that path.
            off, us, cs, codec, meta_len = reader.blobs[skref]
            if codec == CODEC_RAW:
                assert us == cs == len(skeleton)
                record = reader.record_base + off
                physical = record + BHDR.size + meta_len
                poisoned = Path(temp) / "tampered.cmpct"
                shutil.copyfile(archive, poisoned)
                blob = bytearray(poisoned.read_bytes())
                assert bytes(blob[physical:physical + cs]) == skeleton
                blob[physical:physical + cs] = sk_modified
                poisoned.write_bytes(blob)
                with CMPCT(poisoned) as hostile:
                    assert hostile._blob(skref) == sk_modified
                    observed = hostile.read("sample.zip")
                    failure = False
                    try:
                        hostile.verify()
                    except IOError:
                        failure = True
                    report["physical_archive_test"] = "complete"
                    report["physical_read_returned_changed_zip"] = observed == mutated
                    report["physical_verify_rejected"] = failure
                    report["original_archive_sha256"] = sha(archive.read_bytes())
                    report["tampered_archive_sha256"] = sha(poisoned.read_bytes())
        assert report["decoded_oracle_verify_rejected"], "Invalid science: whole verify did not reject"
        assert report["decoded_oracle_read_returned_changed_zip"], (
            "FALSIFIED: regular VZIP read now enforces SHA or changed semantics"
        )
        if report["physical_archive_test"] == "complete":
            assert report["physical_verify_rejected"]
            assert report["physical_read_returned_changed_zip"]
    report["decision"] = "SHA_NOT_ENFORCED_ON_VZIP_READ"
    return report


if __name__ == "__main__":
    evidence = main()
    print(json.dumps(evidence, sort_keys=True, indent=2))
