"""O150 positive repair court for ordinary ZIP export failure-atomicity.

The original O143 defect-expecting source remains unchanged on its own PR.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import tempfile
import zipfile

import pytest

from cmpct.builder import Builder
from cmpct.codec import BHDR, S_BLOB
from cmpct.reader import CMPCT


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def old_zip(path: Path) -> bytes:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("previous/untouched.txt", b"previous-valid-zip: must survive a failed export")
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as zf:
        assert zf.read("previous/untouched.txt") == b"previous-valid-zip: must survive a failed export"
    return raw


def assert_rejected(call) -> str:
    try:
        call()
    except (OSError, ValueError, RuntimeError, EOFError, binascii.Error, zlib_error()) as exc:
        return f"{type(exc).__name__}: {str(exc)[:200]}"
    raise AssertionError("corrupt CMPCT member was accepted unexpectedly")


def zlib_error():
    import zlib
    return zlib.error


def physical_blob_record(ar: CMPCT, blob_index: int) -> tuple[int, tuple]:
    off, usize, csize, codec, mlen = ar.blobs[blob_index]
    pos = ar.record_base + off
    fields = BHDR.unpack_from(ar.mm, pos)
    assert fields[0] == b"CMA4"
    assert fields[1] == codec and fields[4] == usize
    assert fields[5] == csize and fields[6] == mlen
    return pos, fields


def report(case: str, **kw) -> None:
    print("O143_CASE=" + json.dumps({"case": case, **kw}, sort_keys=True), flush=True)


def test_independent_raw_crc_rejection_preserves_prior_zip() -> None:
    """Builder-independent frozen physical RAW: output is opened before CRC rejection."""
    fixture = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    vec = next(v for v in fixture["vectors"] if v["name"] == "raw.bin")
    frozen = base64.b64decode(vec["archive_base64"])
    assert len(frozen) == vec["archive_bytes"]
    assert digest(frozen) == vec["archive_sha256"]

    with tempfile.TemporaryDirectory(prefix="o143-frozen-") as root:
        d = Path(root)
        source = d / "frozen.cmpct"
        source.write_bytes(frozen)
        target = d / "previous.zip"
        prior = old_zip(target)
        with CMPCT(source) as ar:
            assert ar.read("raw.bin") == bytes(range(64))
            assert digest(ar.read("raw.bin")) == vec["logical_sha256"]
            ar.export_zip(d / "control.zip")
        with zipfile.ZipFile(d / "control.zip") as zf:
            assert zf.read("raw.bin") == bytes(range(64))

        with CMPCT(source) as ar:
            row = ar.by["raw.bin"]
            assert row[6][0] == S_BLOB
            pos, fields = physical_blob_record(ar, row[6][1])
            assert fields[1] == 0  # RAW; do not test the separately owned direct-Deflate path.
            # BHDR layout: magic/codec/flags/reserved/usize/csize/meta_len/CRC/SHA.
            crc_offset = pos + struct.calcsize("<4sBBHQQI")
            assert crc_offset == pos + 28
        modified = bytearray(frozen)
        modified[crc_offset] ^= 0x01
        source.write_bytes(modified)
        assert digest(source.read_bytes()) != digest(frozen)
        with CMPCT(source) as ar:
            read_error = assert_rejected(lambda: ar.read("raw.bin"))
            export_error = assert_rejected(lambda: ar.export_zip(target))
        after = target.read_bytes()
        assert after == prior, ("prior ZIP changed after failed export", len(after))
        assert zipfile.is_zipfile(target)
        with zipfile.ZipFile(target) as zf:
            assert zf.read("previous/untouched.txt") == b"previous-valid-zip: must survive a failed export"
        assert not list(d.glob(".cmpct-zip-*.tmp"))
        assert source.stat().st_size == len(frozen)
        report("frozen_raw_crc", result="prior_regular_zip_preserved",
               archive_before_sha=digest(frozen), archive_after_sha=digest(source.read_bytes()),
               target_before_sha=digest(prior), target_after_sha=digest(after),
               target_before_bytes=len(prior), target_after_bytes=len(after),
               read_error=read_error, export_error=export_error)


def test_builder_two_member_late_corruption_preserves_prior_zip() -> None:
    """Separate genuine Builder-controlled product case: a good member is already emitted."""
    with tempfile.TemporaryDirectory(prefix="o143-late-") as root:
        d = Path(root)
        src = d / "src"
        src.mkdir()
        good = random.Random(1401).randbytes(96 * 1024)
        bad = random.Random(1402).randbytes(112 * 1024)
        (src / "a_good.bin").write_bytes(good)
        (src / "z_bad.bin").write_bytes(bad)
        archive = d / "two.cmpct"
        Builder(src).build(archive)
        with CMPCT(archive) as ar:
            assert [x[0] for x in ar.files if x[1] == 0] == ["a_good.bin", "z_bad.bin"]
            assert ar.read("a_good.bin") == good
            assert ar.read("z_bad.bin") == bad
            row = ar.by["z_bad.bin"]
            assert row[6][0] == S_BLOB, row[6]
            pos, fields = physical_blob_record(ar, row[6][1])
            assert fields[1] in (0, 1), ("not a RAW/Zstd direct payload", fields[1])
            mutate_pos = pos + BHDR.size + fields[6] + 17
            assert mutate_pos < pos + BHDR.size + fields[6] + fields[5]
            clean_source_sha = digest(archive.read_bytes())
            ar.export_zip(d / "clean.zip")
        with zipfile.ZipFile(d / "clean.zip") as zf:
            assert zf.read("a_good.bin") == good
            assert zf.read("z_bad.bin") == bad

        target = d / "previous.zip"
        prior = old_zip(target)
        changed = bytearray(archive.read_bytes())
        changed[mutate_pos] ^= 0x01
        archive.write_bytes(changed)
        with CMPCT(archive) as ar:
            assert ar.read("a_good.bin") == good
            read_error = assert_rejected(lambda: ar.read("z_bad.bin"))
            export_error = assert_rejected(lambda: ar.export_zip(target))
        partial = target.read_bytes()
        assert partial == prior, ("late member failure changed prior ZIP", len(partial))
        assert zipfile.is_zipfile(target)
        with zipfile.ZipFile(target) as zf:
            assert zf.read("previous/untouched.txt") == b"previous-valid-zip: must survive a failed export"
        assert not list(d.glob(".cmpct-zip-*.tmp"))
        report("builder_late_payload", result="prior_regular_zip_preserved_after_late_failure",
               physical_codec=fields[1], archive_before_sha=clean_source_sha,
               archive_after_sha=digest(archive.read_bytes()),
               target_before_sha=digest(prior), target_after_sha=digest(partial),
               target_before_bytes=len(prior), target_after_bytes=len(partial),
               read_error=read_error, export_error=export_error)


def test_clean_export_swaps_inode_but_preserves_hardlink_old_bytes() -> None:
    """Successful replacement changes inode topology; this is product compatibility debt."""
    fixture = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    vec = next(v for v in fixture["vectors"] if v["name"] == "raw.bin")
    frozen = base64.b64decode(vec["archive_base64"])
    with tempfile.TemporaryDirectory(prefix="o150-replace-") as root:
        d = Path(root)
        source = d / "frozen.cmpct"
        source.write_bytes(frozen)
        target = d / "previous.zip"
        old = old_zip(target)
        os.chmod(target, 0o640)
        alias = d / "old-hardlink.zip"
        os.link(target, alias)
        before = target.stat()
        with CMPCT(source) as ar:
            ar.export_zip(target)
        after = target.stat()
        with zipfile.ZipFile(target) as zf:
            assert zf.read("raw.bin") == bytes(range(64))
        assert (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
        assert alias.read_bytes() == old
        assert (after.st_mode & 0o777) == 0o640
        assert source.read_bytes() == frozen
        assert not list(d.glob(".cmpct-zip-*.tmp"))
        report("clean_regular_replace", result="exact_zip_new_inode_old_hardlink_unchanged",
               target_after_bytes=target.stat().st_size, prior_alias_sha=digest(alias.read_bytes()),
               new_target_sha=digest(target.read_bytes()))


def test_failed_export_does_not_create_new_public_zip() -> None:
    """Stage cleanup when a requested public destination did not exist."""
    fixture = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    vec = next(v for v in fixture["vectors"] if v["name"] == "raw.bin")
    with tempfile.TemporaryDirectory(prefix="o150-no-target-") as root:
        d = Path(root)
        raw = bytearray(base64.b64decode(vec["archive_base64"]))
        source = d / "frozen.cmpct"
        source.write_bytes(raw)
        with CMPCT(source) as ar:
            row = ar.by["raw.bin"]
            pos, _ = physical_blob_record(ar, row[6][1])
        raw[pos + struct.calcsize("<4sBBHQQI")] ^= 1
        source.write_bytes(raw)
        absent = d / "absent.zip"
        with CMPCT(source) as ar:
            error = assert_rejected(lambda: ar.export_zip(absent))
        assert not absent.exists()
        assert not list(d.glob(".cmpct-zip-*.tmp"))
        report("absent_target", result="failed_export_no_public_zip",
               source_after_sha=digest(source.read_bytes()), export_error=error)
