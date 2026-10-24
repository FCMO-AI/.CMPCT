"""Revision-24 hostile filesystem-metadata structural court.

Pre-registered defect: a self-checksummed but unauthenticated index may carry malformed fsmeta rows that
pass preflight and fail only after extraction writes file content. The expected
outcome is early rejection by both independent preflight and the Reader, before
creating a destination. No changes to frozen format bytes or benchmark thresholds.
"""
from __future__ import annotations

from copy import deepcopy
import os

import msgpack
import pytest

from cmpct.codec import FTR, FMAGIC, HDR, sha, zc
from cmpct.core import Builder, CMPCT
from cmpct.validation import ValidationError, preflight_archive


@pytest.fixture
def ordinary_archive(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.bin").write_bytes(b"exact-content-" * 10)
    archive = tmp_path / "original.cmpct"
    Builder(source, workers=1).build(archive)
    assert preflight_archive(archive)["files"] == 1
    return archive


def _authenticated_fsmeta_mutation(archive, mutated, target):
    """Re-sign both physical index copies and the footer; preserve real payload."""
    data = archive.read_bytes()
    magic, ver, flags, comp_len, raw_len, body_len, _ = HDR.unpack_from(data)
    body = data[HDR.size + comp_len:HDR.size + comp_len + body_len]
    with CMPCT(archive) as reader:
        index = deepcopy(reader.index)
    mutated(index["fsmeta"])
    raw = msgpack.packb(index, use_bin_type=True)
    compressed = zc(raw, 12)
    digest = sha(raw)
    target.write_bytes(
        HDR.pack(magic, ver, flags, len(compressed), len(raw), len(body), digest)
        + compressed + body + compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(raw), 0, digest)
    )
    return target


BAD_FS_META = [
    ("xattrs-not-array", lambda meta: meta.update(xattrs=[[0, 7]])),
    ("xattr-row-width", lambda meta: meta.update(xattrs=[[0, [[ "user.good", b"ok"]], "extra"]])),
    ("xattr-key-not-text", lambda meta: meta.update(xattrs=[[0, [[123, b"ok"]]]])),
    ("xattr-value-not-bytes", lambda meta: meta.update(xattrs=[[0, [["user.good", "string"]]]])),
    ("xattr-name-nul", lambda meta: meta.update(xattrs=[[0, [["user.\x00bad", b"ok"]]]])),
    ("xattr-name-empty", lambda meta: meta.update(xattrs=[[0, [["", b"ok"]]]])),
    ("xattr-duplicate-name", lambda meta: meta.update(xattrs=[[0, [["user.good", b"a"], ["user.good", b"b"]]]])),
    ("xattr-duplicate-file", lambda meta: meta.update(xattrs=[[0, [["user.good", b"a"]]], [0, [["user.other", b"b"]]]])),
    ("owner-row-short", lambda meta: meta.update(owner_overrides=[[0, 1000]])),
    ("owner-row-bool", lambda meta: meta.update(owner_overrides=[[0, True, 1000]])),
    ("owner-duplicate-file", lambda meta: meta.update(owner_overrides=[[0, 1, 2], [0, 3, 4]])),
    ("owner-negative-uid", lambda meta: meta.update(owner_overrides=[[0, -1, 42]])),
    ("xattr-pair-width", lambda meta: meta.update(xattrs=[[0, [["user.good", b"ok", b"extra"]]]])),
    ("xattr-pairs-not-array", lambda meta: meta.update(xattrs=[[0, {"user.good": b"ok"}]])),
]


@pytest.mark.parametrize("label,mutation", BAD_FS_META, ids=[x[0] for x in BAD_FS_META])
def test_authenticated_invalid_fsmeta_rejected_before_extraction(
    ordinary_archive, tmp_path, label, mutation
):
    forged = _authenticated_fsmeta_mutation(
        ordinary_archive, mutation, tmp_path / (label + ".cmpct")
    )
    with pytest.raises(ValidationError, match="fsmeta"):
        preflight_archive(forged)
    destination = tmp_path / ("out-" + label)
    with CMPCT(forged) as reader:
        # The Reader must reject before any output is created, not after writing
        # payload.bin and reaching _restore_extra_metadata.
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.extractall(destination)
    assert not destination.exists()


def test_valid_fsmeta_contract_and_reconstruction(ordinary_archive, tmp_path):
    valid = _authenticated_fsmeta_mutation(
        ordinary_archive,
        lambda meta: meta.update(
            owner_overrides=[[0, 1000, 1000]],
            xattrs=[[0, [["user.valid", b"opaque\x00value"]]]],
        ),
        tmp_path / "valid.cmpct",
    )
    assert preflight_archive(valid)["files"] == 1
    with CMPCT(valid) as reader:
        assert reader.read("payload.bin") == b"exact-content-" * 10
        reader.extractall(tmp_path / "valid-output", metadata=False)
    assert (tmp_path / "valid-output" / "payload.bin").read_bytes() == b"exact-content-" * 10

def test_reader_rejects_bad_fsmeta_without_any_explicit_preflight(ordinary_archive, tmp_path):
    """Independent write-boundary test; do not rely on preflight's exception to mask Reader."""
    mutated = _authenticated_fsmeta_mutation(
        ordinary_archive,
        lambda meta: meta.update(xattrs=[[0, [["user.bad", "not-bytes"]]]]),
        tmp_path / "reader-only.cmpct",
    )
    output = tmp_path / "uncreated"
    with CMPCT(mutated) as reader:
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.extractall(output)
    assert not output.exists()


def test_reader_verify_refuses_structurally_invalid_fsmeta(ordinary_archive, tmp_path):
    mutated = _authenticated_fsmeta_mutation(
        ordinary_archive,
        lambda meta: meta.update(owner_overrides=[[0, 10]]),
        tmp_path / "verify-only.cmpct",
    )
    with CMPCT(mutated) as reader:
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.verify()

def test_real_filesystem_xattr_is_preserved_when_supported(tmp_path):
    """Positive control against rejecting Builder-produced nonempty metadata."""
    if not all(hasattr(os, name) for name in ("setxattr", "getxattr", "listxattr")):
        pytest.skip("filesystem xattr API not available")
    source = tmp_path / "positive-src"
    source.mkdir()
    original = source / "payload.bin"
    original.write_bytes(b"\x00" * 128 + b"exact-original")
    try:
        os.setxattr(original, "user.cmpct_posix_test", b"\x00\xff\x10")
    except OSError as exc:
        pytest.skip(f"filesystem does not support user xattrs: {exc}")
    archive = tmp_path / "positive.cmpct"
    Builder(source, workers=1).build(archive)
    assert preflight_archive(archive)["files"] == 1
    destination = tmp_path / "positive-out"
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        reader.extractall(destination, metadata=True)
    copied = destination / "payload.bin"
    assert copied.read_bytes() == original.read_bytes()
    assert os.getxattr(copied, "user.cmpct_posix_test") == b"\x00\xff\x10"
